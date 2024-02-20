from io import BytesIO
import pandas as pd
import streamlit as st
import re
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm

# Define o layout da página para 'wide'
st.set_page_config(layout="wide")

st.title('Converter lista de Endereços para Vazio Sanitário')

def agrupar_por_endereco(df_final):
    df_final['KM'] = pd.to_numeric(df_final['KM'], errors='coerce')
    grouped = df_final.groupby('Endereço')
    data = []
    for name, group in grouped:
        if 'BR 429' in name:
            grouped_by_setor = group.groupby('SETOR')
            for setor, sub_group in grouped_by_setor:
                group_sorted = sub_group.sort_values('KM')
                dados_agrupados = group_sorted.to_dict('records')
                data.append({'Endereço': f"{name} - {setor}", 'Dados Agrupados': dados_agrupados})
        else:
            group_sorted = group.sort_values('KM')
            dados_agrupados = group_sorted.to_dict('records')
            data.append({'Endereço': name, 'Dados Agrupados': dados_agrupados})
    df_agrupado = pd.DataFrame(data)
    return df_agrupado
def process_dataframe(df):
    """
    Processa o DataFrame para extrair informações e adicionar novas colunas.
    """
    df_final = df.copy()
    df_final['Nome da Propriedade'] = df_final['Endereço e Informações'].apply(lambda x: x.split('(')[0].strip())
    df_final['Codigo'] = df_final['Endereço e Informações'].apply(lambda x: re.search(r'\((.*?)\)', x).group(1) if re.search(r'\((.*?)\)', x) else None)
    df_final['Endereço'] = df_final['Endereço e Informações'].apply(lambda x: x.split(')', 1)[1].split(', ')[0].strip() if ')' in x else None)
    df_final['KM'] = pd.to_numeric(df_final['Endereço e Informações'].apply(lambda x: re.search(r'KM\s*(\d+,\d+|\d+)', x).group(1).replace(',', '.') if re.search(r'KM\s*(\d+,\d+|\d+)', x) else None), errors='coerce') 
    df_final['SETOR'] = df_final['Endereço e Informações'].apply(
    lambda x: re.search(r'STR.*?\/(.*?)(\s|$)', x).group(1)[:2] if re.search(r'STR.*?\/(.*?)(\s|$)', x) else None

 
)

    return df_final

def create_pdf(df, filename):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=1*cm, leftMargin=1*cm, topMargin=1*cm, bottomMargin=1*cm)
    
    # Crie uma lista de larguras de coluna
    col_widths = [None] * len(df.columns)  # substitua None por valores específicos de largura como [3*cm, 2*cm, ...]

    data_list = [df.columns.tolist()] + df.values.tolist()
    table = Table(data_list, colWidths=col_widths)

    style = TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ])
    
    # Aplicando efeito zebrado
    for each in range(1, len(data_list), 2):
        style.add('BACKGROUND', (0, each), (-1, each), colors.whitesmoke)
    for each in range(2, len(data_list), 2):
        style.add('BACKGROUND', (0, each), (-1, each), colors.lightgrey)

    table.setStyle(style)

    elements = [table]
    doc.build(elements)

    buffer.seek(0)
    return buffer.getvalue()


def load_and_display_excel():
    uploaded_file = st.file_uploader("Escolha uma planilha Excel", type=['xlsx'])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        df_final = process_dataframe(df)
        st.write("DataFrame carregado:")
        # st.dataframe(df)
        st.write("DataFrame final com as informações selecionadas e a nova coluna 'Nome da Propriedade':")
        st.dataframe(df_final)
        
        df_agrupado = agrupar_por_endereco(df_final)
        st.write("Resultado do agrupamento por 'Endereço', com todos os dados relevantes mantidos:")
        
        for _, row in df_agrupado.iterrows():
            st.subheader(f"Endereço: {row['Endereço']}")
            df_temp = pd.DataFrame(row['Dados Agrupados'])
            st.write(df_temp)
            
            # Ajuste aqui: selecionando as colunas na ordem desejada
            # Supondo que a coluna "Nome" esteja na posição correta em seu DataFrame
            # E ajustando os índices das colunas conforme necessário
            # selected_columns = ['Nome', 'Endereço e Informações', 'Nome do proprietario da terra', 'Nome da Propriedade']
            selected_columns = ['Nome', 'Endereço e Informações', 'Nome do proprietario da terra']
            df_pdf = df_temp[selected_columns]  # Usando os nomes das colunas diretamente
            
            pdf_bytes = create_pdf(df_pdf, row['Endereço'])
            
            st.download_button(label=f"Baixar relatório PDF para {row['Endereço']}",
                               data=pdf_bytes,
                               file_name=f"{row['Endereço']}.pdf",
                               mime="application/pdf",
                               key=f"button_{row['Endereço']}")


# Chamando a função para carregar e exibir o Excel
load_and_display_excel()