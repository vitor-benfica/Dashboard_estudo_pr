
# !streamlit run app_dash.py
import streamlit as st
import pandas as pd
import plotly.express as px
import pyarrow


#populacao_raw = data_from_athena('us-east-1', 'clean-zone', 'clean_serie_populacao_municipios', filters=None)
#populacao_raw.to_parquet('populacao.parquet', index=False)

st.set_page_config(layout='wide')
# Função para centralizar o DataFrame
def style_dataframe(df):
    # Centralizar texto nas células do DataFrame
    return df.style.set_properties(**{'text-align': 'center'}).set_table_styles(
        [{'selector': 'th', 'props': [('text-align', 'center')]}]
    )



#############################

proporcoes=pd.read_parquet('proporcoes.parquet')
df_grouped=pd.read_parquet('df_grouped.parquet')
tx_geom=pd.read_parquet('txa_crescimento.parquet')
idade_escolar_dependencia=pd.read_parquet('idade_escolar.parquet')
mat_idade_raw=pd.read_parquet('mat_idade.parquet')
######### Agrupamento populacao por idade escolar
idade_escolar = idade_escolar_dependencia[['Estado', 'Região Imediata', 'co_municipio','idade_creche', 'idade_preescola', 'idade_edinf','idade_ai', 'idade_af', 'idade_ef', 'idade_em']]
#idade_escolar.rename(columns={'idade_creche': 'Creche','idade_preescola': 'Pré-escola', 'idade_edinf': 'Educação Infantil',    'idade_ai': 'Anos Iniciais',    'idade_af': 'Anos Finais',    'idade_ef': 'Ensino Fundamental',    'idade_em': 'Ensino Médio'}, inplace=True)
idade_escolar=idade_escolar.melt(id_vars=['Estado','Região Imediata', 'co_municipio'], var_name='Grupo Idade', value_name='populacao')
#idade_escolar_gp=idade_escolar.groupby(['Estado','Região Imediata', 'Ano', 'Grupo Idade'])['valor'].sum().reset_index()
#idade_escolar_gp['Grupo Idade'] = pd.Categorical(idade_escolar_gp['Grupo Idade'], categories=['Educação Infantil', 'Creche', 'Pré-escola', 'Ensino Fundamental', 'Anos Finais', 'Anos Iniciais', 'Ensino Médio']
#, ordered=True)
#idade_escolar_gp=idade_escolar_gp.pivot_table(index=['Estado', 'Região Imediata', 'Ano'], columns='Grupo Idade', values='valor').reset_index()
############## Agrupamento de matrículas na idade correta
mat_idade_raw['idade_edinf']= mat_idade_raw['mat_ate_3_anos']+mat_idade_raw['mat_4_a_5_anos']
mat_idade_raw['idade_ef']= mat_idade_raw['mat_6_a_10_anos']+mat_idade_raw['mat_11_a_14_anos']
mat_idade_r=mat_idade_raw.rename(columns={
    'mat_ate_3_anos': 'idade_creche',
    'mat_4_a_5_anos': 'idade_preescola',
    'mat_6_a_10_anos': 'idade_ai',
    'mat_11_a_14_anos': 'idade_af',
    'mat_15_a_17_anos': 'idade_em'
})
mat_idade = mat_idade_r[['Estado', 'Região Imediata', 'co_municipio', 'idade_creche', 'idade_preescola', 'idade_edinf','idade_ai', 'idade_af', 'idade_ef', 'idade_em']]
mat_idade=mat_idade.melt(id_vars=['Estado','Região Imediata', 'co_municipio'], var_name='Grupo Idade', value_name='matriculas')

freq_liq = idade_escolar.merge(mat_idade, on=['Estado', 'co_municipio', 'Região Imediata', 'Grupo Idade'], how='left')

########## Side bar

uf = st.sidebar.selectbox('Estado', df_grouped['Estado'].unique())


# Filtrar o DataFrame com base nas seleções
df_filtered = df_grouped[(df_grouped['Estado'] == uf)]
proporcoes_filtered = proporcoes[(proporcoes['Estado'] == uf) ]
txa_filtered = tx_geom[(tx_geom['Estado'] == uf) ]
freq_liq_ftr = freq_liq[(freq_liq['Estado'] == uf) ]



freq_liq_ftr=freq_liq_ftr.groupby(['Estado','Região Imediata', 'Grupo Idade'])[['populacao','matriculas']].sum().reset_index()

freq_liq_ftr['Frequencia Líquida']= round(freq_liq_ftr['matriculas']/freq_liq_ftr['populacao']*100,2)
freq_liq_ftr= freq_liq_ftr[['Estado','Região Imediata', 'Grupo Idade', 'Frequencia Líquida']]

freq_liq_ftr= freq_liq_ftr.pivot_table(index=['Estado','Região Imediata'], 
                                     columns='Grupo Idade', 
                                     values='Frequencia Líquida')

freq_liq_ftr.rename(columns={'idade_creche': 'Creche','idade_preescola': 'Pré-escola', 'idade_edinf': 'Educação Infantil',    'idade_ai': 'Anos Iniciais',    'idade_af': 'Anos Finais',    'idade_ef': 'Ensino Fundamental',    'idade_em': 'Ensino Médio'}, inplace=True)


freq_liq_ftr2 = freq_liq_ftr[['Educação Infantil', 'Creche', 'Pré-escola', 'Ensino Fundamental', 'Anos Iniciais','Anos Finais',  'Ensino Médio']]






st.header(f'Região de análise: {uf}')
st.markdown("---")
col1, col2 = st.columns(2)
order = df_filtered.groupby('Região Imediata')['População'].sum().sort_values().index
fig_ano = px.area(df_filtered, x='Ano',y='População', color='Região Imediata', category_orders={'Região Imediata': order})
fig_ano.update_layout(yaxis_tickformat='.3s',  # Formatar como porcentagens
                            yaxis=dict(title='População Residente',  # Título do eixo y
                                       gridcolor='lightgrey'))

with col1:
    st.header("População Total")
    st.subheader('População Residente')
    col1.plotly_chart(fig_ano)
footer_html = """<div style='text-align: left;'>

<p>Fonte: IBGE CENSO; IBGE Estimativas populacionais</p>
</div>"""
st.markdown(footer_html, unsafe_allow_html=True)

fig_proporcao = px.area(proporcoes_filtered, x='Ano',y='Proporção', color='Região Imediata', labels={'Proporção':'Proporção'}, category_orders={'Região Imediata': order})
fig_proporcao.update_layout(yaxis_tickformat='.1%',  # Formatar como porcentagens
                            yaxis=dict(title='Proporção',  # Título do eixo y
                                       gridcolor='lightgrey'))
with col2:
    st.header('Proporção da população')
    st.subheader('População por Regiões Imediatas da UF')
    col2.plotly_chart(fig_proporcao)

st.markdown("---")
col3 = st.columns(1)[0]  # Acesso à única coluna na segunda linha

with col3:
    st.header("População total e taxa de crescimento por Região Imediata")
    st.subheader("População em mil habitantes e taxa média entre os anos como percentual")
    st.dataframe(txa_filtered)
st.markdown("---")
col4 = st.columns(1)[0]  # Acesso à única coluna na segunda linha
with col4:
    st.header("Taxa de Frequência escolar Líquida")
    st.subheader("Alunos Matriculados na idade certa")
    st.dataframe(freq_liq_ftr2)
    footer_html = """<div style='text-align: left;'>
    <p>Fonte: IBGE CENSO 2022; INEP Síntese da Educação Básica</p>
    </div>"""
    st.markdown(footer_html, unsafe_allow_html=True)
