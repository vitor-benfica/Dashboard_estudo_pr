import pandas as pd
# População em idade escolar e Razão de dependência


################# população total
populacao = pd.read_parquet('./populacao.parquet')
populacao_selecionada = populacao[['co_municipio', 'no_uf','no_reg_imediata', 'ano']]
populacao_selecionada=populacao_selecionada[populacao_selecionada['ano'] == 2022]
populacao_selecionada=populacao_selecionada[['co_municipio', 'no_uf','no_reg_imediata']]
populacao['ano']=pd.to_datetime(populacao['ano'], format= '%Y')
df = populacao.sort_values(by=['co_municipio','ano'])
df.rename(columns={'valor': 'População', 'no_reg_imediata': 'Região Imediata', 'no_uf':'Estado'}, inplace=True) 


########################################## matrículas idade correta #######################
mat_idade = pd.read_csv('mat_idade.csv')
mat_idade['ano'] = pd.to_numeric(mat_idade['ano'], downcast='integer')
mat_idade=mat_idade[mat_idade['ano'] == 2022]
mat_idade=mat_idade.drop(columns=['ano'])

mat_idade = mat_idade.merge(populacao_selecionada, on=['co_municipio'], how='left')
mat_idade.rename(columns={'no_uf': 'Estado', 'no_reg_imediata':'Região Imediata'}, inplace=True)
mat_idade.to_parquet('mat_idade.parquet')
############################################### populaçao em idade escolar ####################

idade_escolar = pd.read_csv('populacao_idade_escolar.csv')
idade_escolar=idade_escolar[idade_escolar['ano'] == 2022]
idade_escolar['co_municipio'] = pd.to_numeric(idade_escolar['co_municipio'], downcast='integer')
idade_escolar['ano'] = pd.to_numeric(idade_escolar['ano'], downcast='integer')
float_columns = idade_escolar.select_dtypes(include=['float64']).columns
idade_escolar[float_columns] = idade_escolar[float_columns].apply(pd.to_numeric, downcast='float')


idade_escolar = idade_escolar.merge(populacao_selecionada, on=['co_municipio'], how='left')
idade_escolar.rename(columns={'no_uf': 'Estado', 'no_reg_imediata':'Região Imediata'}, inplace=True)

idade_escolar.to_parquet('idade_escolar.parquet')
########################################################################################################

# populacao pormicroregiao
df['Ano']= df['ano'].apply(lambda x: str(x.year))

df_grouped=df.groupby(['Estado','Região Imediata', 'Ano'])['População'].sum().reset_index()

df_grouped.to_parquet('df_grouped.parquet', index=False)
# taxa de crescimento


df_grouped['Ano'] = df_grouped['Ano'].astype(int)
    # Definir os períodos e os anos de interesse para calcular o CAGR
periods = {
    '1980-1991': (1980, 1991),
    '1991-2000': (1991, 2000),
    '2000-2010': (2000, 2010),
    '2010-2022': (2010, 2022)
}

# Dicionário para armazenar DataFrames de CAGR
cagr_dataframes = {}

# Iterar sobre cada período para calcular o CAGR
for period, (start_year, end_year) in periods.items():
    # Filtrar o DataFrame para os anos de interesse para o período atual
    df_txa = df_grouped[df_grouped['Ano'].isin([start_year, end_year])]
    
    # Pivotar os dados para ter 'Ano' como colunas e 'População' como valores
    df_txa_pivot = df_txa.pivot_table(index=['Estado','Região Imediata'], columns='Ano', values='População', aggfunc='sum')
    
    # Verificar se ambos os anos estão presentes no pivot
    if df_txa_pivot.shape[1] == 2:
        # Calcular o CAGR
        num_years = end_year - start_year
        df_txa_pivot[f'Taxa {period}'] = round(((((df_txa_pivot[end_year] / df_txa_pivot[start_year]) ** (1 / num_years)) - 1)*100),2)
        
        # Armazenar o DataFrame no dicionário
        cagr_dataframes[period] = df_txa_pivot.reset_index()
    else:
        print(f'Dados insuficientes para calcular o CAGR para o período {period}')

# Concatenar todos os DataFrames armazenados no dicionário
final_cagr_df = pd.concat(cagr_dataframes.values(), axis=1)

# Remover colunas duplicadas resultantes do reset_index em cada período (como 'Região Imediata')
final_cagr_df = final_cagr_df.loc[:,~final_cagr_df.columns.duplicated()]
final_cagr_df = final_cagr_df.reset_index()

 
    
    # Salvar o DataFrame como arquivo Parquet
final_cagr_df.to_parquet('txa_crescimento.parquet', index=False)

# Proporção da população por mircroregiao
# Suponha que 'df_grouped' seja o DataFrame e que 'População' seja a variável de interesse

# Agrupar por Estado e Mesorregião, e calcular a soma
mesoregiao_soma= df_grouped.groupby(['Estado', 'Região Imediata','Ano']).agg({'População': 'sum'}).rename(columns={'População': 'Total Meso'}).reset_index()

# Agrupar por Estado para obter a soma total por estado
state_sums = df_grouped.groupby(['Estado','Ano']).agg({'População': 'sum'}).rename(columns={'População': 'Soma Estado'}).reset_index()

# Juntar os dois resultados para calcular proporções
proporcoes = mesoregiao_soma.merge(state_sums, on=['Estado','Ano'])
proporcoes['Proporção'] = proporcoes['Total Meso'] / proporcoes['Soma Estado']
proporcoes.to_parquet('proporcoes.parquet', index=False)

################### Rascunhho

# Lista das colunas a serem ajustadas
columns_to_round = ['1980', '1991', '2000', '2010', '2022']
# Arredonda as colunas para duas casas decimais
tx_geom[columns_to_round] = tx_geom[columns_to_round].round(1).astype(str)
tx_geom = tx_geom.applymap(lambda x: str(x).replace('.', ','))
tx_geom=  tx_geom.drop('index', axis=1)