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
        "--drop",
        action="store_true",
        help="Apaga a tabela completamente em vez de apenas limpar o conteúdo."
    )
    parser.add_argument(
        "table_name",
        nargs='?',
        default=None,
        help="O nome da tabela a ser limpa. Se não for fornecido, lista as tabelas."
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
    elif args.drop:
        drop_table(engine, args.table_name)
    else:
        clear_table(engine, args.table_name)

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

def drop_table(engine, table_name: str):
    """Apaga completamente uma tabela específica do banco de dados após confirmação."""
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
        print("A estrutura da tabela também será removida.")
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

def clear_table(engine, table_name: str):
    """Limpa todo o conteúdo de uma tabela específica do banco de dados após confirmação."""
    try:
        with engine.connect() as conn:
            # Verifica se a tabela existe
            result = conn.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}')")
            exists = result.fetchone()[0]
            
            if not exists:
                print(f"\nErro: A tabela '{table_name}' não existe no banco de dados.")
                list_tables(engine)
                return

            # Conta os registros antes de limpar
            result = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
            count_before = result.fetchone()[0]

            print("\n" + "="*50)
            print(f"ATENÇÃO: Você está prestes a limpar todo o conteúdo da tabela '{table_name}'.")
            print(f"A tabela contém {count_before} registros.")
            print("Esta ação não pode ser desfeita, mas a estrutura da tabela será mantida.")
            print("="*50 + "\n")
            
            confirm = input(f"Digite '{table_name}' para confirmar a limpeza: ")

            if confirm == table_name:
                # Limpa a tabela
                conn.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
                print(f"\n✅ Tabela '{table_name}' limpa com sucesso.")
                print(f"   {count_before} registros foram removidos.")
            else:
                print("\n❌ Operação cancelada. A tabela não foi alterada.")

    except SQLAlchemyError as e:
        print(f"\nErro durante a operação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()