import argparse
import sys
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.exc import SQLAlchemyError

def main():
    """Função principal do script."""
    
    # URL do banco de dados PostgreSQL (Docker)
    database_url = "postgresql://alugueis_user:alugueis_password@localhost:5432/alugueis"

    parser = argparse.ArgumentParser(
        description="Script para listar ou apagar tabelas do banco de dados da aplicação AlugueisV4.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "table_name",
        nargs='?',
        default=None,
        help="O nome da tabela a ser apagada. Se não for fornecido, lista as tabelas."
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Força a listagem de todas as tabelas disponíveis e sai."
    )

    args = parser.parse_args()

    try:
        engine = create_engine(database_url)
        # Testa a conexão
        with engine.connect() as conn:
            print("✅ Conexão com o banco de dados PostgreSQL estabelecida com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao conectar com o banco de dados: {e}")
        print(f"URL do banco: {database_url}")
        print("Certifique-se de que o container Docker do PostgreSQL está rodando.")
        sys.exit(1)

    if args.list or not args.table_name:
        list_tables(engine)
    else:
        delete_table(engine, args.table_name)

def list_tables(engine):
    """Lista todas as tabelas no banco de dados."""
    meta = MetaData()
    try:
        meta.reflect(bind=engine)
        print("Tabelas disponíveis no banco de dados:")
        if not meta.tables:
            print("- Nenhuma tabela encontrada.")
            return
        for table_name in sorted(meta.tables.keys()):
            print(f"- {table_name}")
    except SQLAlchemyError as e:
        print(f"\nErro ao conectar ou ler o banco de dados: {e}")
        sys.exit(1)

def delete_table(engine, table_name: str):
    """Apaga uma tabela específica do banco de dados após confirmação."""
    meta = MetaData()
    try:
        meta.reflect(bind=engine)
        
        if table_name not in meta.tables:
            print(f"\nErro: A tabela '{table_name}' não existe no banco de dados.")
            list_tables(engine)
            return

        table_to_delete = meta.tables[table_name]

        print("\n" + "="*50)
        print(f"ATENÇÃO: Você está prestes a apagar permanentemente a tabela '{table_name}'.")
        print("Esta ação não pode ser desfeita e todos os dados serão perdidos.")
        print("="*50 + "\n")
        
        confirm = input(f"Digite '{table_name}' para confirmar a exclusão: ")

        if confirm == table_name:
            table_to_delete.drop(engine)
            print(f"\n✅ Tabela '{table_name}' apagada com sucesso.")
        else:
            print("\n❌ Operação cancelada. A tabela não foi apagada.")

    except SQLAlchemyError as e:
        print(f"\nErro durante a operação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()