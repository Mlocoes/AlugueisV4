#!/usr/bin/env python3
"""
Script para migrar dados do SQLite para PostgreSQL
"""
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
from datetime import datetime
from app.core.database import engine, Base

def migrate_data():
    # Configurações
    sqlite_db = 'alugueis.db'
    postgres_config = {
        'host': 'localhost',
        'database': 'alugueis',
        'user': 'alugueis_user',
        'password': 'alugueis_password',
        'port': '5432'
    }

    print("🚀 Iniciando migração de SQLite para PostgreSQL...")

    # Conectar ao SQLite
    print("📖 Conectando ao SQLite...")
    sqlite_conn = sqlite3.connect(sqlite_db)
    sqlite_cursor = sqlite_conn.cursor()

    # Conectar ao PostgreSQL
    print("📗 Conectando ao PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(**postgres_config)
        pg_cursor = pg_conn.cursor()
    except Exception as e:
        print(f"❌ Erro ao conectar ao PostgreSQL: {e}")
        print("💡 Certifique-se de que o contêiner PostgreSQL está rodando:")
        print("   docker-compose up -d db")
        return

    try:
        # Criar tabelas no PostgreSQL
        print("🔨 Criando tabelas no PostgreSQL...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas!")

        # Migrar usuários
        print("👥 Migrando usuários...")
        sqlite_cursor.execute("SELECT id, username, nome, sobrenome, tipo, email, telefone, documento, tipo_documento, endereco, hashed_password, ativo FROM usuarios")
        usuarios = sqlite_cursor.fetchall()

        if usuarios:
            # Limpar tabela destino
            pg_cursor.execute("TRUNCATE TABLE usuarios RESTART IDENTITY CASCADE")

            # Converter valores booleanos
            usuarios_convertidos = []
            for usuario in usuarios:
                usuario_lista = list(usuario)
                # Converter ativo (posição 11) para boolean
                usuario_lista[11] = bool(usuario_lista[11])
                usuarios_convertidos.append(tuple(usuario_lista))

            # Inserir dados (sem criado_em e atualizado_em pois serão preenchidos automaticamente)
            execute_values(pg_cursor, """
                INSERT INTO usuarios (id, username, nome, sobrenome, tipo, email, telefone, documento, tipo_documento, endereco, hashed_password, ativo)
                VALUES %s
            """, usuarios_convertidos)
            print(f"✅ Migrados {len(usuarios)} usuários")

        # Migrar imóveis
        print("🏠 Migrando imóveis...")
        sqlite_cursor.execute("SELECT id, nome, endereco, tipo, area_total, area_construida, valor_catastral, valor_mercado, iptu_anual, condominio, alugado, ativo FROM imoveis")
        imoveis = sqlite_cursor.fetchall()

        if imoveis:
            pg_cursor.execute("TRUNCATE TABLE imoveis RESTART IDENTITY CASCADE")
            
            # Converter valores booleanos
            imoveis_convertidos = []
            for imovel in imoveis:
                imovel_lista = list(imovel)
                # Converter alugado (posição 10) e ativo (posição 11) para boolean
                imovel_lista[10] = bool(imovel_lista[10])
                imovel_lista[11] = bool(imovel_lista[11])
                imoveis_convertidos.append(tuple(imovel_lista))
            
            execute_values(pg_cursor, """
                INSERT INTO imoveis (id, nome, endereco, tipo, area_total, area_construida, valor_catastral, valor_mercado, iptu_anual, condominio, alugado, ativo)
                VALUES %s
            """, imoveis_convertidos)
            print(f"✅ Migrados {len(imoveis)} imóveis")

        # Migrar aluguéis mensais
        print("💰 Migrando aluguéis mensais...")
        sqlite_cursor.execute("SELECT id, id_imovel, id_proprietario, data_referencia, valor_total, valor_proprietario, taxa_administracao, status FROM alugueis_mensais")
        alugueis_mensais = sqlite_cursor.fetchall()

        if alugueis_mensais:
            pg_cursor.execute("TRUNCATE TABLE alugueis_mensais RESTART IDENTITY CASCADE")
            
            # Truncar valores muito grandes
            alugueis_convertidos = []
            for aluguel in alugueis_mensais:
                aluguel_lista = list(aluguel)
                # Truncar valores muito grandes (limite aproximado para NUMERIC(12,2))
                for i in [4, 5, 6]:  # índices dos campos numéricos
                    if aluguel_lista[i]:
                        valor = abs(float(aluguel_lista[i]))
                        if valor > 9999999999.99:
                            aluguel_lista[i] = 9999999999.99
                        elif valor < 0:
                            aluguel_lista[i] = 0
                        else:
                            aluguel_lista[i] = round(valor, 2)
                alugueis_convertidos.append(tuple(aluguel_lista))
            
            execute_values(pg_cursor, """
                INSERT INTO alugueis_mensais (id, id_imovel, id_proprietario, data_referencia, valor_total, valor_proprietario, taxa_administracao, status)
                VALUES %s
            """, alugueis_convertidos)
            print(f"✅ Migrados {len(alugueis_mensais)} aluguéis mensais")

        # Migrar participações
        print("📊 Migrando participações...")
        sqlite_cursor.execute("SELECT id, id_imovel, id_proprietario, participacao, data_cadastro FROM participacoes")
        participacoes = sqlite_cursor.fetchall()

        if participacoes:
            pg_cursor.execute("TRUNCATE TABLE participacoes RESTART IDENTITY CASCADE")
            execute_values(pg_cursor, """
                INSERT INTO participacoes (id, id_imovel, id_proprietario, participacao, data_cadastro)
                VALUES %s
            """, participacoes)
            print(f"✅ Migradas {len(participacoes)} participações")

        # Commit das mudanças
        pg_conn.commit()
        print("🎉 Migração concluída com sucesso!")

        # Verificar contagens
        print("\n📊 Verificação final:")
        for table in ['usuarios', 'imoveis', 'alugueis_mensais', 'participacoes']:
            pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = pg_cursor.fetchone()[0]
            print(f"   {table}: {count} registros")

    except Exception as e:
        print(f"❌ Erro durante migração: {e}")
        pg_conn.rollback()

    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate_data()
