from brain import rodar_sync, discover_reload_site
from website.data_loader import load_team_table
import plotly.express as px
import streamlit as st
import pandas as pd
import base64
import os

class Pages():
    def __init__(self, logic):
        self.logic = logic

    def tables(self):
        opções = ["times", "maps", "agents", "comps", "camps", "partidas", "mapas_jogados", "players"]

        col_logo, col_titulo = st.columns([1, 5])

        with col_logo:
            st.image("./assets/logo.png", width=120)

        with col_titulo:
            st.markdown("<h1 style='text-align: center;'>VlrBot Site</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center;'>Este é um site que proporciona uma visualização alternativa do VlrBot.</p>", unsafe_allow_html=True)

        st.divider()

        col_com, col_graf, col_filt = st.columns([1, 2, 1])

        with col_com:
            dado = None
            st.subheader("Parametros")
            nome_dado = st.selectbox("Selecione o dado a ser exibido", opções)
            dado = rodar_sync(self.logic.get_value(nome_dado))
            if dado is not None:
                executar = True

        with col_graf:
            st.subheader("Visualização")
            st.write(f"Exibindo o dado: {nome_dado}")
            if executar:
                st.table(dado)
            else:
                st.write("Selecione um dado para exibir.")

        with col_filt:
            st.subheader("Filtros")
            st.write("Filtros ainda não implementados.")

        # Footer com CSS Fixo na parte inferior da tela
        st.markdown(
            """
            <style>
            .footer {
                position: fixed;
                left: 0;
                bottom: 0;
                width: 100%;
                background-color: rgba(14, 17, 23, 0.95); /* Cor padrão escura do Streamlit com transparência */
                color: #888888;
                text-align: center;
                padding: 10px 0;
                font-size: 13px;
                border-top: 1px solid #262730;
                z-index: 999;
            }
            </style>
            <div class="footer">
                <p>📊 Dados extraídos do VLR.gg • Cache limpa em janelas de 12 horas UTC • Banco de Dados: Neon Tech</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    def info_time(self):
        opções = rodar_sync(self.logic.get_value("times"))
        opções = {time["tag"]: time["id"] for time in opções}

        col_logo, col_titulo, disc = st.columns([1, 5, 1])

        with col_logo:
            st.image("./assets/logo.png", width=120)

        with col_titulo:
            st.markdown("<h1 style='text-align: center;'>VlrBot Site</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center;'>Este é um site que proporciona uma visualização alternativa do VlrBot.</p>", unsafe_allow_html=True)
        
        with disc:
            st.markdown(
                """
                <style>
                /* Alveja todos os botões de link do Streamlit */
                div[data-testid="stLinkButton"] > a {
                    background-color: #5865F2 !important; /* Verde brilhante */
                    color: #FFFFFF !important;            /* Texto preto para contraste */
                    border: 2px solid #5865F2 !important;
                    padding: 20px 40px !important;        /* Ajusta a ALTURA (20px top/bottom) e largura */
                    font-weight: bold !important;
                    border-radius: 8px !important;
                }
                
                /* Efeito de Hover (passar o mouse) */
                div[data-testid="stLinkButton"] > a:hover {
                    background-color: #4752C4 !important;
                    border-color: #4752C4 !important;
                    color: #FFFFFF !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.link_button("Discord", "https://discord.gg/CQjRzfhvFw", use_container_width=True)

        st.divider()

        col_com, espaço, col_graf = st.columns([2, 1, 8])

        with col_com:
            dado = None
            nome_dado = None
            executar = False
            pagina = None

            st.subheader("Parametros")
            nome_dado = st.selectbox("Selecione o time a ser exibido", options=opções.keys(), index=None, placeholder="Selecione um time")
            stats_table = load_team_table(opções.get(nome_dado), discover_reload_site())
            if nome_dado is not None:

                dado = rodar_sync(self.logic.info_time(nome_dado, preTable=stats_table))

            pagina = st.selectbox("Selecione a página a ser exibida", options=["Overview", "Maps"], index=0, placeholder="Selecione uma página")

            if dado is not None and pagina is not None:
                executar = True

            if pagina == "Maps" and dado is not None:
                mapa_selecionado = st.selectbox("Selecione o mapa a ser exibido", options=["Geral"] + [mapa["nome"] for mapa in dado[2]], index=0, placeholder="Selecione um mapa")


        with col_graf:
            esp1, col0, esp2 = st.columns([1, 4, 1.7])
            with col0:
                st.markdown("<h2 style='text-align: center;'>Visualização</h2>", unsafe_allow_html=True)
            
            if executar:
                time, matches_decript, time_mapas, time_stats = dado

                paginas_lista = []

                colunas = ["Rating", "ACS", "KD", "KAST", "ADR", "KPR", "APR", "FKPR", "FDPR", "HS"]

                # Stats do Embed 1
                colunas = ["Rating", "ACS", "KD", "KAST", "ADR", "KPR", "APR", "FKPR", "FDPR", "HS"]
                idx_mais_recente = time_stats["Camp"].idxmax()
                stats_recente = time_stats.loc[idx_mais_recente]
                mapas_jogados_geral = 0
                Atk_geral = [0, 0] # [vitórias, total]
                Def_geral = [0, 0] # [vitórias, total]
                Map_geral = [0, 0] # [vitórias, total]

                win = "\u2588\u200a"
                lose = "\u2591\u200a"

                # EMBED 2->8 - Mapas
                pool = []
                for mapa in time_mapas:
                    pool.append(mapa["nome"])

                    mapas_jogados_geral += mapa["info"]["played"]
                    Atk_geral[0] += mapa['info']['atk_'][0]
                    Atk_geral[1] += mapa['info']['atk_'][1]
                    Def_geral[0] += mapa['info']['def_'][0]
                    Def_geral[1] += mapa['info']['def_'][1]
                    Map_geral[0] += mapa['info']['map_'][0]
                    Map_geral[1] += mapa['info']['map_'][1]

                    mapa_jogado = mapa["info"]["played"]
                    Atk = mapa['info']['atk_'][0] / mapa['info']['atk_'][1] if mapa['info']['atk_'][1] > 0 else 0
                    Def = mapa['info']['def_'][0] / mapa['info']['def_'][1] if mapa['info']['def_'][1] > 0 else 0
                    Map = mapa['info']['map_'][0] / mapa['info']['map_'][1] if mapa['info']['map_'][1] > 0 else 0
                    Atk_emoji = win * int(Atk * 10) + lose * (10 - int(Atk * 10))
                    Def_emoji = win * int(Def * 10) + lose * (10 - int(Def * 10))
                    Map_emoji = win * int(Map * 10) + lose * (10 - int(Map * 10))

                    Mapa = {
                        "nome": f"{mapa['nome']}",
                        "description": {
                            "jogado": mapa_jogado,
                            "atk": Atk,
                            "def": Def,
                            "map": Map
                        },
                        "composicoes": []
                    }

                    
                    composicoes = mapa["descricao"][:-1].split("\n") # [:-1] para remover a última quebra de linha
                    for comp in composicoes[:9]:
                        infos = comp.split("|")
                        name = infos[0]
                        value = ""
                        if len(infos) > 1:
                            value += f"{infos[1]}\n"
                            for info in infos[2:]:
                                value += f"- {info}\n"
                        else:
                            name = comp
                            value = "\u200b"
                            
                        Mapa["composicoes"].append({"name": name, "value": value})

                    paginas_lista.append(Mapa)

                if pagina == "Overview":
                    col12, col11, esp = st.columns([1, 4, 1.7])

                    with col12:
                        # Renderiza a logo do time com um leve espaçamento inferior
                        st.markdown(
                            f"""
                            <div style='text-align: left;'>
                                <img src='{time["img_url"]}' width='100' style='object-fit: contain; margin-bottom: 5px;'>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )

                    with col11:
                        # Alinha verticalmente os textos para casar com a altura da logo de 100px
                        st.markdown(
                            f"""
                            <div style='padding-top: 10px;'>
                                <h1 style='text-align: center; margin: 0; padding: 0; line-height: 1.1;'>{time['tag']}</h1>
                                <h5 style='text-align: center; margin: 0; color: #888888; font-weight: normal; margin-top: 5px;'>
                                    🌍 {time['regiao']}'s franchise team
                                </h5>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                    
                    st.divider()

                    # Infos gerais de win rate
                    Atk_ = Atk_geral[0]/Atk_geral[1] if Atk_geral[1] > 0 else 0
                    Atk_emoji = win * int(Atk_ * 10) + lose * (10 - int(Atk_ * 10))
                    Def_ = Def_geral[0]/Def_geral[1] if Def_geral[1] > 0 else 0
                    Def_emoji = win * int(Def_ * 10) + lose * (10 - int(Def_ * 10))
                    Map_ = Map_geral[0]/Map_geral[1] if Map_geral[1] > 0 else 0
                    Map_emoji = win * int(Map_ * 10) + lose * (10 - int(Map_ * 10))
                    
                    col1, col2, col3= st.columns([1, 1, 1])
                    with col1:
                        for i, coluna in enumerate(colunas):
                            if i % 3 == 0:
                                if coluna in ["KAST", "HS"]:
                                    st.metric(label=coluna, value=f"{stats_recente[coluna]*100:.2f}%")
                                else:
                                    st.metric(label=coluna, value=f"{stats_recente[coluna]:.2f}")
                    with col2:
                        for i, coluna in enumerate(colunas):
                            if i % 3 == 1:
                                if coluna in ["KAST", "HS"]:
                                    st.metric(label=coluna, value=f"{stats_recente[coluna]*100:.2f}%")
                                else:
                                    st.metric(label=coluna, value=f"{stats_recente[coluna]:.2f}")
                            
                        st.metric(label="Clutches", value=f"{stats_recente['CLw']}/{stats_recente['CLp']}")

                    with col3:
                        for i, coluna in enumerate(colunas):
                            if i % 3 == 2:
                                if coluna in ["KAST", "HS"]:
                                    st.metric(label=coluna, value=f"{stats_recente[coluna]*100:.2f}%")
                                else:
                                    st.metric(label=coluna, value=f"{stats_recente[coluna]:.2f}")
                    
                    st.divider()

                    st.markdown(
                        """
                        <div style='text-align: center; margin-top: 20px; margin-bottom: 10px;'>
                            <h2 style='margin: 0; padding: 0;'>📊 Informações Gerais do Time</h2>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

                    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

                    with col1:
                        st.write(f"Mapas jogados: ")
                        st.write(f"#### {mapas_jogados_geral}")
                    with col2:
                        st.write(f"Winrate Ataque: ({Atk_ * 100:.0f}%)")
                        st.write(f"#### {Atk_emoji}")
                    with col3:
                        st.write(f"Winrate Defesa: ({Def_ * 100:.0f}%)")
                        st.write(f"#### {Def_emoji}")
                    with col4:
                        st.write(f"Winrate Geral: ({Map_ * 100:.0f}%)")
                        st.write(f"#### {Map_emoji}")

                    st.divider()

                    st.markdown(
                        """
                        <div style='text-align: center; margin-top: 25px; margin-bottom: 20px;'>
                            <h3 style='margin: 0; padding: 0;'>⚔️ Últimas Partidas</h3>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

                    for match in matches_decript[:-1].split("\n"):
                        if not match.strip():
                            continue
                            
                        match_parts = match.split(" ")
                        
                        nome_campeonato = ' '.join(match_parts[1:-3])
                        team_left_id = match_parts[-3].split(":")[1].lower() 
                        placar = match_parts[-2]
                        team_right_id = match_parts[-1].split(":")[1].lower()
                        
                        caminho_esq = f"./assets/teams/{team_left_id}.png"
                        caminho_dir = f"./assets/teams/{team_right_id}.png"
                        
                        if not os.path.exists(caminho_esq): caminho_esq = "./assets/teams/default.png"
                        if not os.path.exists(caminho_dir): caminho_dir = "./assets/teams/default.png"

                        with st.container(border=True):
                            st.markdown(f"<div style='text-align: center; color: #888888; font-size: 11px; font-weight: bold; margin-bottom: 5px;'>🏆 {nome_campeonato}</div>", unsafe_allow_html=True)
                            
                            # 5 colunas para travar as logos e o placar bem colados no centro do card
                            c_esp1, c_img1, c_placar, c_img2, c_esp2 = st.columns([1.5, 2.7, 2.5, 1, 1])
                            
                            with c_img1:
                                st.image(caminho_esq, width=40)
                                
                            with c_placar:
                                st.markdown(f"<div style='font-size: 20px; font-weight: 900; color: #ffffff; padding-top: 3px;'>{placar}</div>", unsafe_allow_html=True)
                                
                            with c_img2:
                                st.image(caminho_dir, width=40)

                elif pagina == "Maps":
                    if mapa_selecionado == "Geral":
                        col12, col11, esp = st.columns([1, 4, 1.7])

                        with col12:
                            # Renderiza a logo do time com um leve espaçamento inferior
                            st.markdown(
                                f"""
                                <div style='text-align: left;'>
                                    <img src='{time["img_url"]}' width='100' style='object-fit: contain; margin-bottom: 5px;'>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )

                        with col11:
                            # Alinha verticalmente os textos para casar com a altura da logo de 100px
                            st.markdown(
                                f"""
                                <div style='padding-top: 10px;'>
                                    <h1 style='text-align: center; margin: 0; padding: 0; line-height: 1.1;'>{time['tag']}</h1>
                                    <h5 style='text-align: center; margin: 0; color: #888888; font-weight: normal; margin-top: 5px;'>
                                        🌍 {time['regiao']}'s franchise team
                                    </h5>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                        
                        st.divider()
                        map_df = pd.DataFrame([{"Mapa": mapa["nome"], "Winrate": mapa["description"]["map"], "jogado": mapa["description"]["jogado"]} for mapa in paginas_lista])
                        AtkDef_df = pd.DataFrame([{"Mapa": mapa["nome"], "W% Ataque": mapa["description"]["atk"], "W% Defesa": mapa["description"]["def"], "jogado": mapa["description"]["jogado"]} for mapa in paginas_lista])

                        fig = px.bar(
                            map_df, 
                            x="Mapa", 
                            y="Winrate", 
                            labels={"Winrate": "Porcentagem (%)", "Mapa": "Mapas"}, 
                            title="Winrate de Mapa"
                        )
                        for idx, row in AtkDef_df.iterrows():
                            fig.add_annotation(
                                x=row["Mapa"],
                                y=.05,
                                text=f"Jogado: {row['jogado']} vezes",
                                showarrow=False,
                                font=dict(color="#ffffff", size=11, family="Arial"),
                                bgcolor="rgba(38, 39, 48, 0.95)", # Fundo escuro sutil para o modo dark do Streamlit
                                bordercolor="#ff4b4b",            # Borda vermelha de aviso
                                borderwidth=1,
                                borderpad=6
                            )
                        fig.update_xaxes(tickangle=0)
                        fig.update_yaxes(tickformat=".0%", range=[0, 1])
                        st.plotly_chart(fig, width='stretch')

                        fig = px.bar(
                            AtkDef_df,
                            x="Mapa",
                            y=["W% Ataque", "W% Defesa"],
                            title="Winrate de Ataque vs. Defesa por Mapa",
                            barmode="group",
                            color_discrete_map={"W% Ataque": "#ef4444", "W% Defesa": "#3b82f6"},
                            labels={"value": "Porcentagem (%)", "variable": "Métrica", "Mapa": "Mapas"}
                        )
                        for idx, row in AtkDef_df.iterrows():
                            fig.add_annotation(
                                x=row["Mapa"],
                                y=.05,
                                text=f"Jogado: {row['jogado']} vezes",
                                showarrow=False,
                                font=dict(color="#ffffff", size=11, family="Arial"),
                                bgcolor="rgba(38, 39, 48, 0.95)",
                                bordercolor="#ff4b4b",
                                borderwidth=1,
                                borderpad=6
                            )

                        fig.update_xaxes(tickangle=0)
                        fig.update_yaxes(tickformat=".0%", range=[0, 1])
                        st.plotly_chart(fig, width='stretch')

                    else:
                        for pag in paginas_lista:
                            if pag["nome"] == mapa_selecionado:
                                mapa_view = pag
                                break

                        col12, col11, esp = st.columns([1, 4, 1.7])

                        with col12:
                            # Renderiza a logo do time com um leve espaçamento inferior
                            st.markdown(
                                f"""
                                <div style='text-align: left;'>
                                    <img src='{time["img_url"]}' width='100' style='object-fit: contain; margin-bottom: 5px;'>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )

                        with col11:
                            # Alinha verticalmente os textos para casar com a altura da logo de 100px
                            st.markdown(
                                f"""
                                <div style='padding-top: 10px;'>
                                    <h1 style='text-align: center; margin: 0; padding: 0; line-height: 1.1;'>{time['tag']}</h1>
                                    <h5 style='text-align: center; margin: 0; color: #888888; font-weight: normal; margin-top: 5px;'>
                                        🌍 {time['regiao']}'s franchise team
                                    </h5>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                        
                        st.divider()
                        
                        comps_lista = []

                        col_comps, esp, col_logo = st.columns([3, 0.5, 1])

                        for i, comp in enumerate(mapa_view["composicoes"]):                            
                            with col_comps:

                                col_id, agt1, agt2, agt3, agt4, agt5= st.columns([3, 1, 1, 1, 1, 1])

                                cmp_name = comp["name"].split(":")

                                if len(cmp_name) == 1:
                                    st.write("### Sem dados disponíveis (Mapa não jogado).")
                                    continue

                                with col_id:
                                    st.write(f"##### Composição {i+1}:")
                                
                                colunas_agentes = [agt1, agt2, agt3, agt4, agt5]
                                indices_agentes = [1, 3, 5, 7, 9]
                                
                                for col, idx in zip(colunas_agentes, indices_agentes):
                                    with col:
                                        st.image(f"./assets/agents/{cmp_name[idx]}.png", width=50)

                                db_sketch = comp["value"].split("\n")[:-1]

                                jogado = db_sketch[0].split(" ")[1]

                                def limpar_porcentagem(texto):
                                    val = texto.split("= ")[1]
                                    return float(val.replace("%", "").strip()) * .01

                                atk_win = limpar_porcentagem(db_sketch[1])
                                def_win = limpar_porcentagem(db_sketch[2])
                                map_win = limpar_porcentagem(db_sketch[3])

                                comps_lista.append({
                                    "Comp": f"Comp {i+1}", 
                                    "Jogado": jogado, 
                                    "W% Ataque": atk_win, 
                                    "W% Defesa": def_win, 
                                    "W% Geral": map_win
                                })

                        if len(comps_lista) > 0:
                            comp_df = pd.DataFrame(comps_lista)

                            fig = px.bar(
                                comp_df,
                                x="Comp",
                                y=['W% Ataque', 'W% Defesa', 'W% Geral'],
                                title="Winrates das Composições (%)",
                                barmode="group",
                                color_discrete_map={"W% Ataque": "#ef4444", "W% Defesa": "#3b82f6", "W% Geral": "#10b981"},
                                labels={"value": "Porcentagem (%)", "variable": "Métrica", "Comp": "Composições"}
                            )
                            for idx, row in comp_df.iterrows():
                                fig.add_annotation(
                                    x=row["Comp"],
                                    y=.05,
                                    text=f"Jogado: {row['Jogado']} vezes",
                                    showarrow=False,
                                    font=dict(color="#ffffff", size=11, family="Arial"),
                                    bgcolor="rgba(38, 39, 48, 0.95)",
                                    bordercolor="#ff4b4b",
                                    borderwidth=1,
                                    borderpad=6
                                )

                            fig.update_xaxes(tickangle=0)
                            fig.update_yaxes(tickformat=".0%", range=[0, 1])
        
                            st.plotly_chart(fig, width='stretch')

            else:
                st.write("Selecione um dado para exibir.")

        # Footer com CSS Fixo na parte inferior da tela
        st.markdown(
            """
            <style>
            .footer {
                position: fixed;
                left: 0;
                bottom: 0;
                width: 100%;
                background-color: rgba(14, 17, 23, 0.95); /* Cor padrão escura do Streamlit com transparência */
                color: #888888;
                text-align: center;
                padding: 10px 0;
                font-size: 13px;
                border-top: 1px solid #262730;
                z-index: 999;
            }
            </style>
            <div class="footer">
                <p>📊 Dados extraídos do VLR.gg • Cache limpa em janelas de 12 horas UTC • Banco de Dados: Neon Tech</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    def help(self):
        info = rodar_sync(self.logic.get_value("times"))

        col_logo, col_titulo, disc = st.columns([1, 5, 1])

        with col_logo:
            st.image("./assets/logo.png", width=120)

        with col_titulo:
            st.markdown("<h1 style='text-align: center;'>VlrBot Site</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center;'>Este é um site que proporciona uma visualização alternativa do VlrBot.</p>", unsafe_allow_html=True)
        
        with disc:
            st.markdown(
                """
                <style>
                /* Alveja todos os botões de link do Streamlit */
                div[data-testid="stLinkButton"] > a {
                    background-color: #5865F2 !important; /* Verde brilhante */
                    color: #FFFFFF !important;            /* Texto preto para contraste */
                    border: 2px solid #5865F2 !important;
                    padding: 20px 40px !important;        /* Ajusta a ALTURA (20px top/bottom) e largura */
                    font-weight: bold !important;
                    border-radius: 8px !important;
                }
                
                /* Efeito de Hover (passar o mouse) */
                div[data-testid="stLinkButton"] > a:hover {
                    background-color: #4752C4 !important;
                    border-color: #4752C4 !important;
                    color: #FFFFFF !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.link_button("Discord", "https://discord.gg/CQjRzfhvFw", use_container_width=True)
        
        st.divider()

        col_com, espaço, col_graf = st.columns([2, 1, 8])

        with col_com:
            st.subheader("Parametros")
            st.write(f"Aqui é onde você pode selecionar os parâmetros dos comandos. Esses parâmetros podem variar entre times, mapas, ou tipo de informação que será mostrada na seção de Visualização")
            st.write(f"Alguns exemplos para você brincar:")
            opções = [time["regiao"] for time in info]
            opções = list(set(opções))
            nome_dado = st.multiselect("Selecionador de regiões", options=opções, placeholder="Selecione regiões para visualizar")

            comando = st.selectbox("Selecione um dos nossos comandos", options=["Info_time", "Times_vs"], index=None, placeholder="Selecione um comando")

        with col_graf:
            esp1, col0, esp2 = st.columns([1, 4, 1.7])
            with col0:
                st.markdown("<h2 style='text-align: center;'>Visualização</h2>", unsafe_allow_html=True)

            st.write(f"Aqui é onde as informações que você busca encontrar vão aparecer! \
                      As formas como as informações estão distribuídas são semelhantes ao do bot do discord, \
                     para que você não tenha que reaprender. Como bônus, temos alguns gráficos visuais aqui também!")
            if len(nome_dado) == 0:
                pass
            else:
                text = ""
                colunas = []
                for regiao in nome_dado:
                    text += f"{regiao}, "
                st.write(f"Você selecionou: {text[:-2]}. (Remova as seleções para remover essa sessão)")
                st.write("Você pode usar as tags abaixo para procurar pelos times que quer ver nos comandos. É mais fácil escrever o comecinho do que caçar entre as opções 😉")
                
                for i in nome_dado:
                    colunas.append(1)
                colunas = st.columns(colunas)

                for i, regiao in enumerate(nome_dado):
                    with colunas[i]:
                        st.markdown(f"<h2 style='text-align: center;'>{regiao}</h2>", unsafe_allow_html=True)
                        col1, col2 = st.columns([1, 1])
                        for time in info:
                            if time["regiao"] == regiao:
                                with col1:
                                    st.markdown(f"<p style='text-align: right; font-size: 19px'>{time['tag']}</h2>", unsafe_allow_html=True)
                                with col2:
                                    st.image(f"{time['img_url']}", width=30)

            if comando is None:
                pass
            elif comando == "Info_time":
                st.write("Ficou curioso sobre o /info_time, é?\
                          Esse foi o primeiro comando criado para o VlrBot.\
                          Ele permite consultar informações sobre um time específico.\
                          Essas informações são relacionadas à winrates de mapa, de ataque e de defesa.\
                          Também tempos informações sobre composições usadas em cada mapa e quais as respectivas winrates dessa composição.")
                st.write("Coisas para saber sobre o comando:")
                st.write("- Se você for o primeiro usuário a selecionar determinado time depois das 7:30 ou 19:30,\
                          o comando deve demorar um pouco mais para rodar!")
                st.write("- Ao selecionar a página Maps, você vai ser direcionado para uma página com as infos gerais de winrate de mapas.\
                          Você pode então selecionar um mapa para ver, e então terá acesso à composições usadas e suas respectivas winrates também!")
                st.write("- Ao selecionar um mapa específico, você vai ver as 9 últimas composições usadas!\
                          Além disso, é legal saber que as composições que aparecem primerio e, logo, tem números menores, são mais recentes (Salvo exceções de problemas no banco de dados.)!")
            
            elif comando == "Times_vs":
                st.write("O /time_vs é basicamente um comando para acompanhar jogos!\
                          Você seleciona dois times, e nós rodamos dois /info_time, um para cada time selecionado.\
                          No discord, você inclusive seleciona os mapas que quer visualizar.\
                          Aqui você vê todos. Mas como temos gráficos, fica até mais fácil comparar!")
                st.write("Coisas para saber sobre o comando:")
                st.write("- Se você for o primeiro usuário a selecionar determinado time depois das 7:30 ou 19:30,\
                          o comando deve demorar um pouco mais para rodar, igual o /info_time!")
                st.write("- Na página de overview, os stats agora aparecem em comparação. O lado em negrito é o que está com o maior número (Mas nem sempre isso é bom...)")
                st.write("- A aba de mapas 'Geral' agora pode estar mais confusa. Mas relaxa, o time da esquerda é sempre vermelho\
                          enquanto o time da direita é sempre azul! Na parte de Ataque e Defesa, cores escuras são ataque, cores claras são defesa.\
                          Nós temos legendas que podem ajudá-lo a se encontrar se ainda estiver confuso.")
                st.write ("- Nos gráficos, você vai encontrar uma sessão com algo próximo de `A:X|B:Y`.\
                          Isso significa que o time A (da esquerda) jogou determinado mapa X vezes e que o time B (direita) jogou Y vezes.")
                st.write("- Para não poluir muito a aba dos mapas, nesse comando as composições foram limitadas para até 3 composições. \
                          Assim como no \info_times, as composições com números menores são as mais recentes (A menos que tenha dado algum erro no banco de dados...)")

        st.markdown(
            """
            <style>
            .footer {
                position: fixed;
                left: 0;
                bottom: 0;
                width: 100%;
                background-color: rgba(14, 17, 23, 0.95); /* Cor padrão escura do Streamlit com transparência */
                color: #888888;
                text-align: center;
                padding: 10px 0;
                font-size: 13px;
                border-top: 1px solid #262730;
                z-index: 999;
            }
            </style>
            <div class="footer">
                <p>📊 Dados extraídos do VLR.gg • Cache limpa em janelas de 12 horas UTC • Banco de Dados: Neon Tech</p>
            </div>
            """,
            unsafe_allow_html=True
        )        

    def vs(self):
        opções = rodar_sync(self.logic.get_value("times"))
        opções = {time["tag"]: time["id"] for time in opções}

        col_logo, col_titulo, disc = st.columns([1, 5, 1])

        with col_logo:
            st.image("./assets/logo.png", width=120)

        with col_titulo:
            st.markdown("<h1 style='text-align: center;'>VlrBot Site</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center;'>Este é um site que proporciona uma visualização alternativa do VlrBot.</p>", unsafe_allow_html=True)
        
        with disc:
            st.markdown(
                """
                <style>
                /* Alveja todos os botões de link do Streamlit */
                div[data-testid="stLinkButton"] > a {
                    background-color: #5865F2 !important; /* Verde brilhante */
                    color: #FFFFFF !important;            /* Texto preto para contraste */
                    border: 2px solid #5865F2 !important;
                    padding: 20px 40px !important;        /* Ajusta a ALTURA (20px top/bottom) e largura */
                    font-weight: bold !important;
                    border-radius: 8px !important;
                }
                
                /* Efeito de Hover (passar o mouse) */
                div[data-testid="stLinkButton"] > a:hover {
                    background-color: #4752C4 !important;
                    border-color: #4752C4 !important;
                    color: #FFFFFF !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            st.link_button("Discord", "https://discord.gg/CQjRzfhvFw", use_container_width=True)
            
        st.divider()

        col_com, espaço, col_graf = st.columns([2, 1, 8])

        with col_com:
            dado1 = None
            dado2 = None
            executar = False
            pagina = None

            st.subheader("Parametros")
            nome_times = st.multiselect("Selecione o time a ser exibido", options=opções.keys(), placeholder="Selecione um time", max_selections=2)
            if len(nome_times) == 2:
                
                if nome_times[0] is not None:
                    stats_table = load_team_table(opções.get(nome_times[0]), discover_reload_site())
                    dado1 = rodar_sync(self.logic.info_time(nome_times[0], preTable=stats_table))

                if nome_times[1] is not None:
                    stats_table = load_team_table(opções.get(nome_times[1]), discover_reload_site())
                    dado2 = rodar_sync(self.logic.info_time(nome_times[1], preTable=stats_table))

            pagina = st.selectbox("Selecione a página a ser exibida", options=["Overview", "Maps"], index=0, placeholder="Selecione uma página")

            if dado1 is not None and dado2 is not None:
                executar = True

            if pagina == "Maps" and dado1 is not None and dado2 is not None:
                mapa_selecionado = st.selectbox("Selecione o mapa a ser exibido", options=["Geral"] + [mapa["nome"] for mapa in dado1[2]], index=0, placeholder="Selecione um mapa")

        with col_graf:
            st.markdown("<h2 style='text-align: center;'>Visualização</h2>", unsafe_allow_html=True)
            if executar:
                time1, matches_decript1, time_mapas1, time_stats1 = dado1
                time2, matches_decript2, time_mapas2, time_stats2 = dado2

                paginas_lista1 = []
                paginas_lista2 = []

                colunas = ["Rating", "ACS", "KD", "KAST", "ADR", "KPR", "APR", "FKPR", "FDPR", "HS"]

                # Stats do Embed 1
                colunas = ["Rating", "ACS", "KD", "KAST", "ADR", "KPR", "APR", "FKPR", "FDPR", "HS"]
                idx_mais_recente1 = time_stats1["Camp"].idxmax()
                idx_mais_recente2 = time_stats2["Camp"].idxmax()

                stats_recente1 = time_stats1.loc[idx_mais_recente1]
                stats_recente2 = time_stats2.loc[idx_mais_recente2]

                mapas_jogados_geral1 = 0
                Atk_geral1 = [0, 0] # [vitórias, total]
                Def_geral1 = [0, 0] # [vitórias, total]
                Map_geral1 = [0, 0] # [vitórias, total]
                mapas_jogados_geral2 = 0
                Atk_geral2 = [0, 0] # [vitórias, total]
                Def_geral2 = [0, 0] # [vitórias, total]
                Map_geral2 = [0, 0] # [vitórias, total]

                # EMBED 2->8 - Mapas
                pool = []
                for mapa1, mapa2 in zip(time_mapas1, time_mapas2):
                    pool.append(mapa1["nome"])

                    mapas_jogados_geral1 += mapa1["info"]["played"]
                    Atk_geral1[0] += mapa1['info']['atk_'][0]
                    Atk_geral1[1] += mapa1['info']['atk_'][1]
                    Def_geral1[0] += mapa1['info']['def_'][0]
                    Def_geral1[1] += mapa1['info']['def_'][1]
                    Map_geral1[0] += mapa1['info']['map_'][0]
                    Map_geral1[1] += mapa1['info']['map_'][1]

                    mapas_jogados_geral2 += mapa2["info"]["played"]
                    Atk_geral2[0] += mapa2['info']['atk_'][0]
                    Atk_geral2[1] += mapa2['info']['atk_'][1]
                    Def_geral2[0] += mapa2['info']['def_'][0]
                    Def_geral2[1] += mapa2['info']['def_'][1]
                    Map_geral2[0] += mapa2['info']['map_'][0]
                    Map_geral2[1] += mapa2['info']['map_'][1]

                    mapa_jogado1 = mapa1["info"]["played"]
                    Atk1 = mapa1['info']['atk_'][0] / mapa1['info']['atk_'][1] if mapa1['info']['atk_'][1] > 0 else 0
                    Def1 = mapa1['info']['def_'][0] / mapa1['info']['def_'][1] if mapa1['info']['def_'][1] > 0 else 0
                    Map1 = mapa1['info']['map_'][0] / mapa1['info']['map_'][1] if mapa1['info']['map_'][1] > 0 else 0

                    mapa_jogado2 = mapa2["info"]["played"]
                    Atk2 = mapa2['info']['atk_'][0] / mapa2['info']['atk_'][1] if mapa2['info']['atk_'][1] > 0 else 0
                    Def2 = mapa2['info']['def_'][0] / mapa2['info']['def_'][1] if mapa2['info']['def_'][1] > 0 else 0
                    Map2 = mapa2['info']['map_'][0] / mapa2['info']['map_'][1] if mapa2['info']['map_'][1] > 0 else 0

                    Mapa1 = {
                        "nome": f"{mapa1['nome']}",
                        "description": {
                            "jogado": mapa_jogado1,
                            "atk": Atk1,
                            "def": Def1,
                            "map": Map1
                        },
                        "composicoes": []
                    }

                    Mapa2 = {
                        "nome": f"{mapa2['nome']}",
                        "description": {
                            "jogado": mapa_jogado2,
                            "atk": Atk2,
                            "def": Def2,
                            "map": Map2
                        },
                        "composicoes": []
                    }

                    
                    composicoes = mapa1["descricao"][:-1].split("\n") # [:-1] para remover a última quebra de linha
                    for comp in composicoes[:3]:
                        infos = comp.split("|")
                        name = infos[0]
                        value = ""
                        if len(infos) > 1:
                            value += f"{infos[1]}\n"
                            for info in infos[2:]:
                                value += f"- {info}\n"
                        else:
                            name = comp
                            value = "\u200b"
                            
                        Mapa1["composicoes"].append({"name": name, "value": value})

                    paginas_lista1.append(Mapa1)

                    composicoes = mapa2["descricao"][:-1].split("\n") # [:-1] para remover a última quebra de linha
                    for comp in composicoes[:3]:
                        infos = comp.split("|")
                        name = infos[0]
                        value = ""
                        if len(infos) > 1:
                            value += f"{infos[1]}\n"
                            for info in infos[2:]:
                                value += f"- {info}\n"
                        else:
                            name = comp
                            value = "\u200b"
                            
                        Mapa2["composicoes"].append({"name": name, "value": value})

                    paginas_lista2.append(Mapa2)

                if pagina == "Overview":
                    col11, col_label, col12 = st.columns([2, 1, 2])
                    with col11:
                        st.markdown(
                            f"""
                            <div style='text-align: right; padding-right: 20px;'>
                                <img src='{time1["img_url"]}' width='100' style='object-fit: contain; margin-bottom: 10px;'>
                                <h2 style='margin: 0; color: #ef4444; padding: 0;'>{time1['tag']}</h2>
                                <h5 style='margin: 0; color: #888888; font-weight: normal;'>{time1['regiao']}'s team</h5>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )

                    with col_label:
                        st.markdown(
                            """
                            <div style='text-align: center; padding-top: 45px;'>
                                <h1 style='margin: 0; color: #ff4b4b; font-style: italic; font-weight: 900;'>VS</h1>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )

                    with col12:
                        st.markdown(
                            f"""
                            <div style='text-align: left; padding-left: 20px;'>
                                <img src='{time2["img_url"]}' width='100' style='object-fit: contain; margin-bottom: 10px;'>
                                <h2 style='margin: 0; color: #3b82f6; padding: 0;'>{time2['tag']}</h2>
                                <h5 style='margin: 0; color: #888888; font-weight: normal;'>{time2['regiao']}'s team</h5>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )


                    # Infos gerais de win rate
                    Atk1_ = Atk_geral1[0]/Atk_geral1[1] if Atk_geral1[1] > 0 else 0
                    Def1_ = Def_geral1[0]/Def_geral1[1] if Def_geral1[1] > 0 else 0
                    Map1_ = Map_geral1[0]/Map_geral1[1] if Map_geral1[1] > 0 else 0

                    Atk2_ = Atk_geral2[0]/Atk_geral2[1] if Atk_geral2[1] > 0 else 0
                    Def2_ = Def_geral2[0]/Def_geral2[1] if Def_geral2[1] > 0 else 0
                    Map2_ = Map_geral2[0]/Map_geral2[1] if Map_geral2[1] > 0 else 0
                    

                    st.markdown("<h3 style='text-align: center;'>⚔️ Comparação Direta de Equipes ⚔️</h3>", unsafe_allow_html=True)
                    st.write("")

                    for coluna in colunas:
                        val_t1 = stats_recente1[coluna]
                        val_t2 = stats_recente2[coluna]

                        if coluna in ["KAST", "HS"]:
                            texto_t1 = f"{val_t1 * 100:.2f}%"
                            texto_t2 = f"{val_t2 * 100:.2f}%"

                            pct_bar_t1 = min(float(val_t1), 1.0)
                            pct_bar_t2 = min(float(val_t2), 1.0)
                        else:
                            texto_t1 = f"{val_t1:.2f}"
                            texto_t2 = f"{val_t2:.2f}"
                            
                            max_valor = max(val_t1, val_t2, 0.001) 
                            pct_bar_t1 = float(val_t1 / max_valor)
                            pct_bar_t2 = float(val_t2 / max_valor)

                        c_val1, c_bar1, c_nome, c_bar2, c_val2 = st.columns([1, 2, 1.5, 2, 1])

                        estilo_t1 = "font-weight: bold; color: #FFFFFF;" if val_t1 >= val_t2 else "font-weight: normal; color: #888888;"
                        estilo_t2 = "font-weight: bold; color: #FFFFFF;" if val_t2 >= val_t1 else "font-weight: normal; color: #888888;"

                        with c_val1:
                            st.markdown(f"<div style='text-align: right; {estilo_t1}'>{texto_t1}</div>", unsafe_allow_html=True)
                            
                        with c_bar1:
                            st.progress(pct_bar_t1)
                            
                        with c_nome:
                            st.markdown(f"<div style='text-align: center; color: gray; font-weight: bold;'>{coluna}</div>", unsafe_allow_html=True)
                            
                        with c_bar2:
                            st.progress(pct_bar_t2)
                            
                        with c_val2:
                            st.markdown(f"<div style='text-align: left; {estilo_t2}'>{texto_t2}</div>", unsafe_allow_html=True)
                    
                    cl_w1, cl_p1 = stats_recente1['CLw'], stats_recente1['CLp']
                    cl_w2, cl_p2 = stats_recente2['CLw'], stats_recente2['CLp']

                    tx_cl1 = (cl_w1 / cl_p1) if cl_p1 > 0 else 0.0
                    tx_cl2 = (cl_w2 / cl_p2) if cl_p2 > 0 else 0.0
                    max_tx = max(tx_cl1, tx_cl2, 0.001)

                    c_val1, c_bar1, c_nome, c_bar2, c_val2 = st.columns([1, 2, 1.5, 2, 1])
                    with c_val1:
                        st.markdown(f"<div style='text-align: right;'>{cl_w1}/{cl_p1}</div>", unsafe_allow_html=True)
                    with c_bar1:
                        st.progress(tx_cl1 / max_tx)
                    with c_nome:
                        st.markdown("<div style='text-align: center; color: gray; font-weight: bold;'>Clutches (W/P)</div>", unsafe_allow_html=True)
                    with c_bar2:
                        st.progress(tx_cl2 / max_tx)
                    with c_val2:
                        st.markdown(f"<div style='text-align: left;'>{cl_w2}/{cl_p2}</div>", unsafe_allow_html=True)


                    st.markdown("<h3 style='text-align: center; margin-top: 20px;'>📊 Informações Gerais das Equipes</h3>", unsafe_allow_html=True)
                    st.markdown("<p style='text-align: center; color: gray; margin-bottom: 25px;'>Volume total de partidas computadas na temporada</p>", unsafe_allow_html=True)

                    col11, col_label, col12 = st.columns([2, 1, 2])

                    with col11:
                        st.markdown(
                            f"""
                            <div style='text-align: right; padding-right: 20px;'>
                                <img src='{time1["img_url"]}' width='70' style='object-fit: contain; margin-bottom: 10px; opacity: 0.8;'>
                                <div style='color: gray; font-size: 14px; font-weight: bold; text-transform: uppercase;'>Mapas Jogados</div>
                                <h2 style='margin: 0; padding: 0; color: #ef4444; font-size: 36px;'>{mapas_jogados_geral1}</h2>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )

                    with col_label:
                        st.markdown(
                            """
                            <div style='text-align: center; padding-top: 35px;'>
                                <h2 style='margin: 0; color: #ff4b4b; font-style: italic; font-weight: 900; opacity: 0.5;'>VS</h2>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )

                    with col12:
                        st.markdown(
                            f"""
                            <div style='text-align: left; padding-left: 20px;'>
                                <img src='{time2["img_url"]}' width='70' style='object-fit: contain; margin-bottom: 10px; opacity: 0.8;'>
                                <div style='color: gray; font-size: 14px; font-weight: bold; text-transform: uppercase;'>Mapas Jogados</div>
                                <h2 style='margin: 0; padding: 0; color: #3b82f6; font-size: 36px;'>{mapas_jogados_geral2}</h2>
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )

                    dados_confronto = [
                        {"Métrica": "Ataque", "Time": time1["tag"], "Winrate": Atk1_},
                        {"Métrica": "Ataque", "Time": time2["tag"], "Winrate": Atk2_},
                        
                        {"Métrica": "Defesa", "Time": time1["tag"], "Winrate": Def1_},
                        {"Métrica": "Defesa", "Time": time2["tag"], "Winrate": Def2_},
                        
                        {"Métrica": "Mapa", "Time": time1["tag"], "Winrate": Map1_},
                        {"Métrica": "Mapa", "Time": time2["tag"], "Winrate": Map2_},
                    ]
                    df_comparacao = pd.DataFrame(dados_confronto)

                    fig = px.bar(
                        df_comparacao,
                        x="Métrica",        
                        y="Winrate",        
                        color="Time",      
                        barmode="group",    
                        title="Comparação de Aproveitamento no Mapa (%)",
                        labels={"Winrate": "Winrate (%)"},
                        color_discrete_map={time1["tag"]: "#ef4444", time2["tag"]: "#3b82f6"} 
                    )

                    fig.update_xaxes(tickangle=0)
                    fig.update_yaxes(tickformat=".0%", range=[0, 1])
                    st.plotly_chart(fig, width='stretch')

                    def renderizar_cards_partidas(matches_decript):
                        if not matches_decript:
                            st.markdown("<p style='color: gray; font-style: italic;'>Nenhuma partida recente registrada.</p>", unsafe_allow_html=True)
                            return

                        for match_str in matches_decript[:-1].split("\n"):
                            if not match_str.strip():
                                continue
                                
                            match_parts = match_str.split(" ")
                            
                            nome_campeonato = ' '.join(match_parts[1:-3])
                            team_left_id = match_parts[-3].split(":")[1].lower()
                            placar = match_parts[-2]
                            team_right_id = match_parts[-1].split(":")[1].lower()
                            
                            caminho_esq = f"./assets/teams/{team_left_id}.png"
                            caminho_dir = f"./assets/teams/{team_right_id}.png"
                            
                            if not os.path.exists(caminho_esq): caminho_esq = "./assets/teams/default.png"
                            if not os.path.exists(caminho_dir): caminho_dir = "./assets/teams/default.png"


                            with st.container(border=True):
                                st.markdown(f"<div style='text-align: center; color: #888888; font-size: 11px; font-weight: bold; margin-bottom: 5px;'>🏆 {nome_campeonato}</div>", unsafe_allow_html=True)
                                
                                c_esp1, c_img1, c_placar, c_img2, c_esp2 = st.columns([1.5, 1, 2, 1, 1.5])
                                
                                with c_img1:
                                    st.image(caminho_esq, width=35)
                                    
                                with c_placar:
                                    st.markdown(f"<div style='text-align: center; font-size: 20px; font-weight: 900; color: #ffffff; padding-top: 3px;'>{placar}</div>", unsafe_allow_html=True)
                                    
                                with c_img2:
                                    st.image(caminho_dir, width=35)

                    st.markdown("<h3 style='text-align: center; margin-top: 25px;'>⚔️ Últimas Partidas</h3>", unsafe_allow_html=True)
                    st.write("")

                    col_t1, col_t2 = st.columns([1, 1])

                    with col_t1:
                        st.markdown(f"<h4 style='text-align: center; color: #ef4444; margin-bottom: 15px;'>{time1['tag']}</h4>", unsafe_allow_html=True)
                        renderizar_cards_partidas(matches_decript1)

                    with col_t2:
                        st.markdown(f"<h4 style='text-align: center; color: #3b82f6; margin-bottom: 15px;'>{time2['tag']}</h4>", unsafe_allow_html=True)
                        renderizar_cards_partidas(matches_decript2)

                elif pagina == "Maps":
                    if mapa_selecionado == "Geral":
                        col11, col_label, col12 = st.columns([2, 1, 2])
                        with col11:
                            st.markdown(
                                f"""
                                <div style='text-align: right; padding-right: 20px;'>
                                    <img src='{time1["img_url"]}' width='100' style='object-fit: contain; margin-bottom: 10px;'>
                                    <h2 style='margin: 0; color: #ef4444; padding: 0;'>{time1['tag']}</h2>
                                    <h5 style='margin: 0; color: #888888; font-weight: normal;'>{time1['regiao']}'s team</h5>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )

                        with col_label:
                            st.markdown(
                                """
                                <div style='text-align: center; padding-top: 45px;'>
                                    <h1 style='margin: 0; color: #ff4b4b; font-style: italic; font-weight: 900;'>VS</h1>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )

                        with col12:
                            st.markdown(
                                f"""
                                <div style='text-align: left; padding-left: 20px;'>
                                    <img src='{time2["img_url"]}' width='100' style='object-fit: contain; margin-bottom: 10px;'>
                                    <h2 style='margin: 0; color: #3b82f6; padding: 0;'>{time2['tag']}</h2>
                                    <h5 style='margin: 0; color: #888888; font-weight: normal;'>{time2['regiao']}'s team</h5>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )


                        map_confronto = []
                        AtkDef_confronto = []

                        tag_a = time1["tag"]
                        tag_b = time2["tag"]

                        for pag_t1, pag_t2 in zip(paginas_lista1, paginas_lista2):
                            map_confronto.append({"Time": tag_a, "Mapa": pag_t1["nome"], "Winrate": pag_t1["description"]["map"], "jogado": pag_t1["description"]["jogado"]})
                            map_confronto.append({"Time": tag_b, "Mapa": pag_t2["nome"], "Winrate": pag_t2["description"]["map"], "jogado": pag_t2["description"]["jogado"]})
                            
                            AtkDef_confronto.append({"Time": tag_a, "Mapa": pag_t1["nome"], "W% Ataque": pag_t1["description"]["atk"], "W% Defesa": pag_t1["description"]["def"], "jogado": pag_t1["description"]["jogado"]})
                            AtkDef_confronto.append({"Time": tag_b, "Mapa": pag_t2["nome"], "W% Ataque": pag_t2["description"]["atk"], "W% Defesa": pag_t2["description"]["def"], "jogado": pag_t2["description"]["jogado"]})

                        map_df = pd.DataFrame(map_confronto)
                        AtkDef_df = pd.DataFrame(AtkDef_confronto)

                        mapas_jogos = {}
                        for item in AtkDef_confronto:
                            if item["Mapa"] not in mapas_jogos:
                                mapas_jogos[item["Mapa"]] = {}
                            mapas_jogos[item["Mapa"]][item["Time"]] = item["jogado"]

                        def formatar_eixo_x(row):
                            mapa = row["Mapa"]
                            jogos_a = mapas_jogos.get(mapa, {}).get(tag_a, 0)
                            jogos_b = mapas_jogos.get(mapa, {}).get(tag_b, 0)
                            return f"{mapa}<br><span style='font-size:13px; color:#888888;'>{tag_a}:{jogos_a} | {tag_b}:{jogos_b}</span>"
                        
                        map_df["Mapa_Detalhado"] = map_df.apply(formatar_eixo_x, axis=1)

                        fig = px.bar(
                            map_df,
                            x="Mapa_Detalhado",        
                            y="Winrate",        
                            color="Time",      
                            barmode="group",    
                            title="Comparação de Aproveitamento no Mapa (%)",
                            labels={"Winrate": "Winrate (%)", "Mapa_Detalhado": "Mapas"},
                            color_discrete_map={tag_a: "#ef4444", tag_b: "#3b82f6"} 
                        )
                        
                        fig.update_xaxes(tickangle=0)
                        fig.update_yaxes(tickformat=".0%", range=[0, 1])
                        st.plotly_chart(fig, width='stretch')

                        # AtkDef

                        AtkDef_df["Mapa_Com_Jogos"] = AtkDef_df.apply(
                            lambda row: f"{row['Mapa']}<br><span style='font-size:10px; color:gray;'>{tag_a}:{row['jogado']} | {tag_b}:{row['jogado']}</span>", 
                            axis=1
                        )

                        AtkDef_df["Mapa_Detalhado"] = AtkDef_df.apply(formatar_eixo_x, axis=1)

                        AtkDef_df2 = pd.melt(
                            AtkDef_df, 
                            id_vars=["Time", "Mapa_Detalhado"], 
                            value_vars=["W% Ataque", "W% Defesa"],
                            var_name="Lado",
                            value_name="Winrate"
                        )
                        AtkDef_df2["Lado do Time"] = AtkDef_df2["Lado"] + " (" + AtkDef_df2["Time"] + ")"

                        cores_customizadas = {
                            f"W% Ataque ({tag_a})": "#b91c1c",  # Vermelho Escuro
                            f"W% Defesa ({tag_a})": "#fca5a5",  # Azul Escuro
                            f"W% Ataque ({tag_b})": "#1d4ed8",  # Vermelho Claro/Pastel
                            f"W% Defesa ({tag_b})": "#93c5fd"   # Azul Claro/Pastel
                        }

                        fig = px.bar(
                            AtkDef_df2,
                            x="Mapa_Detalhado",
                            y="Winrate",
                            color="Lado do Time",
                            barmode="group",
                            title="Confronto Direto de Execução (Ataque vs Defesa) por Mapa",
                            color_discrete_map=cores_customizadas,
                            labels={"Mapa_Detalhado": "Mapas", "Winrate": "Winrate (%)"}
                        )

                        fig.update_xaxes(tickangle=0)
                        fig.update_yaxes(tickformat=".0%", range=[0, 1])

                        fig.update_traces(
                            hovertemplate="<b>%{x}</b><br>Winrate: %{y:.2f}%<extra></extra>"
                        )

                        # Renderiza no Streamlit ocupando a largura total
                        st.plotly_chart(fig, use_container_width=True)

                        

                    else:
                        col11, col_label, col12 = st.columns([2, 1, 2])
                        with col11:
                            st.markdown(
                                f"""
                                <div style='text-align: right; padding-right: 20px;'>
                                    <img src='{time1["img_url"]}' width='100' style='object-fit: contain; margin-bottom: 10px;'>
                                    <h2 style='margin: 0; color: #ef4444; padding: 0;'>{time1['tag']}</h2>
                                    <h5 style='margin: 0; color: #888888; font-weight: normal;'>{time1['regiao']}'s team</h5>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )

                        with col_label:
                            st.markdown(
                                """
                                <div style='text-align: center; padding-top: 45px;'>
                                    <h1 style='margin: 0; color: #ff4b4b; font-style: italic; font-weight: 900;'>VS</h1>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )

                        with col12:
                            st.markdown(
                                f"""
                                <div style='text-align: left; padding-left: 20px;'>
                                    <img src='{time2["img_url"]}' width='100' style='object-fit: contain; margin-bottom: 10px;'>
                                    <h2 style='margin: 0; color: #3b82f6; padding: 0;'>{time2['tag']}</h2>
                                    <h5 style='margin: 0; color: #888888; font-weight: normal;'>{time2['regiao']}'s team</h5>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )

                        st.divider()

                        for pag_t1, pag_t2 in zip(paginas_lista1, paginas_lista2):
                            if pag_t1["nome"] == mapa_selecionado:
                                mapa_view1 = pag_t1
                                mapa_view2 = pag_t2
                                break
                        
                        comps1_lista = []
                        comps2_lista = []

                        col_comps1, esp, col_comps2 = st.columns([3, 0.5, 3])

                        # Time 1
                        for i, comp in enumerate(mapa_view1["composicoes"]):                            
                            with col_comps1:

                                col_id, agt1, agt2, agt3, agt4, agt5= st.columns([3, 1, 1, 1, 1, 1])

                                cmp_name = comp["name"].split(":")

                                if len(cmp_name) == 1:
                                    st.write("### Sem dados disponíveis (Mapa não jogado).")
                                    continue

                                with col_id:
                                    st.write(f"##### Composição {i+1}:")
                                
                                colunas_agentes = [agt1, agt2, agt3, agt4, agt5]
                                indices_agentes = [1, 3, 5, 7, 9]
                                
                                for col, idx in zip(colunas_agentes, indices_agentes):
                                    with col:
                                        st.image(f"./assets/agents/{cmp_name[idx]}.png", width=50)

                                db_sketch = comp["value"].split("\n")[:-1]

                                jogado = db_sketch[0].split(" ")[1]

                                def limpar_porcentagem(texto):
                                    val = texto.split("= ")[1]
                                    return float(val.replace("%", "").strip()) * .01

                                atk_win = limpar_porcentagem(db_sketch[1])
                                def_win = limpar_porcentagem(db_sketch[2])
                                map_win = limpar_porcentagem(db_sketch[3])

                                comps1_lista.append({
                                    "Comp": f"Comp {i+1}", 
                                    "Jogado": jogado, 
                                    "W% Ataque": atk_win, 
                                    "W% Defesa": def_win, 
                                    "W% Geral": map_win
                                })
                        
                        # Time 2
                        for i, comp in enumerate(mapa_view2["composicoes"]):                            
                            with col_comps2:

                                col_id, agt1, agt2, agt3, agt4, agt5= st.columns([3, 1, 1, 1, 1, 1])

                                cmp_name = comp["name"].split(":")

                                if len(cmp_name) == 1:
                                    st.write("### Sem dados disponíveis (Mapa não jogado).")
                                    continue

                                with col_id:
                                    st.write(f"##### Composição {i+1}:")
                                
                                colunas_agentes = [agt1, agt2, agt3, agt4, agt5]
                                indices_agentes = [1, 3, 5, 7, 9]
                                
                                for col, idx in zip(colunas_agentes, indices_agentes):
                                    with col:
                                        st.image(f"./assets/agents/{cmp_name[idx]}.png", width=50)

                                db_sketch = comp["value"].split("\n")[:-1]

                                jogado = db_sketch[0].split(" ")[1]

                                def limpar_porcentagem(texto):
                                    val = texto.split("= ")[1]
                                    return float(val.replace("%", "").strip()) * .01

                                atk_win = limpar_porcentagem(db_sketch[1])
                                def_win = limpar_porcentagem(db_sketch[2])
                                map_win = limpar_porcentagem(db_sketch[3])

                                comps2_lista.append({
                                    "Comp": f"Comp {i+1}", 
                                    "Jogado": jogado, 
                                    "W% Ataque": atk_win, 
                                    "W% Defesa": def_win, 
                                    "W% Geral": map_win
                                })

                        col_t1, esp, col_t2 = st.columns([3, 0.5, 3])
                        with col_t1:
                            if len(comps1_lista) > 0:
                                comp_df = pd.DataFrame(comps1_lista)

                                fig = px.bar(
                                    comp_df,
                                    x="Comp",
                                    y=['W% Ataque', 'W% Defesa', 'W% Geral'],
                                    title="Winrates das Composições (%)",
                                    barmode="group",
                                    color_discrete_map={"W% Ataque": "#ef4444", "W% Defesa": "#3b82f6", "W% Geral": "#10b981"},
                                    labels={"value": "Porcentagem (%)", "variable": "Métrica", "Comp": "Composições"}
                                )
                                for idx, row in comp_df.iterrows():
                                    fig.add_annotation(
                                        x=row["Comp"],
                                        y=.05,
                                        text=f"Jogado: {row['Jogado']} vezes",
                                        showarrow=False,
                                        font=dict(color="#ffffff", size=11, family="Arial"),
                                        bgcolor="rgba(38, 39, 48, 0.95)",
                                        bordercolor="#ff4b4b",
                                        borderwidth=1,
                                        borderpad=6
                                    )

                                fig.update_xaxes(tickangle=0)
                                fig.update_yaxes(tickformat=".0%", range=[0, 1])
            
                                st.plotly_chart(fig, width='stretch')
                        with col_t2:
                            if len(comps2_lista) > 0:
                                comp_df = pd.DataFrame(comps2_lista)

                                fig = px.bar(
                                    comp_df,
                                    x="Comp",
                                    y=['W% Ataque', 'W% Defesa', 'W% Geral'],
                                    title="Winrates das Composições (%)",
                                    barmode="group",
                                    color_discrete_map={"W% Ataque": "#ef4444", "W% Defesa": "#3b82f6", "W% Geral": "#10b981"},
                                    labels={"value": "Porcentagem (%)", "variable": "Métrica", "Comp": "Composições"}
                                )
                                for idx, row in comp_df.iterrows():
                                    fig.add_annotation(
                                        x=row["Comp"],
                                        y=.05,
                                        text=f"Jogado: {row['Jogado']} vezes",
                                        showarrow=False,
                                        font=dict(color="#ffffff", size=11, family="Arial"),
                                        bgcolor="rgba(38, 39, 48, 0.95)",
                                        bordercolor="#ff4b4b",
                                        borderwidth=1,
                                        borderpad=6
                                    )

                                fig.update_xaxes(tickangle=0)
                                fig.update_yaxes(tickformat=".0%", range=[0, 1])
            
                                st.plotly_chart(fig, width='stretch')

            else:
                st.write("Selecione um dado para exibir.")

        # Footer com CSS Fixo na parte inferior da tela
        st.markdown(
            """
            <style>
            .footer {
                position: fixed;
                left: 0;
                bottom: 0;
                width: 100%;
                background-color: rgba(14, 17, 23, 0.95); /* Cor padrão escura do Streamlit com transparência */
                color: #888888;
                text-align: center;
                padding: 10px 0;
                font-size: 13px;
                border-top: 1px solid #262730;
                z-index: 999;
            }
            </style>
            <div class="footer">
                <p>📊 Dados extraídos do VLR.gg • Cache limpa em janelas de 12 horas UTC • Banco de Dados: Neon Tech</p>
            </div>
            """,
            unsafe_allow_html=True
        )
