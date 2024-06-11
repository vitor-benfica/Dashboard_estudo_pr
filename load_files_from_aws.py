import os
import pandas as pd
from pyathena import connect
from dotenv import load_dotenv

# Configurações internas
def load_environment():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    env_path = os.path.join(dir_path, '.env')
    load_dotenv(env_path)

def create_athena_connection(region):
    load_environment()  # Garante que as variáveis de ambiente estejam carregadas
    s3_staging_dir = 's3://fgv-municipios-data-lake/athena-sql/'
    return connect(s3_staging_dir=s3_staging_dir, region_name=region)

def data_from_athena(region, database, table, filters=None):
    """
    Carrega dados filtrados de uma tabela AWS Athena usando o Pandas e retorna um DataFrame.

    Args:
        region (str): Região da AWS onde o Athena está localizado.
        database (str): Nome do banco de dados no Athena.
        table (str): Nome da tabela no Athena.
        filters (list, optional): Lista de condições para filtragem dos dados.

    Returns:
        pd.DataFrame: DataFrame contendo os dados lidos e filtrados.
    """
    connection = create_athena_connection(region)
    query = f'SELECT * FROM "{database}"."{table}"'
    if filters:
        query += " WHERE " + " AND ".join(filters)
    df = pd.read_sql(query, connection)
    return df

