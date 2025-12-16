import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

from src.services import SistemaService   # ajuste o caminho se não usar pasta src

service = SistemaService()

# ---------------- CONFIG PÁGINA ----------------
st.set_page_config(
    page_title="Experimento do Tanque de Água",
    page_icon="💧",
    layout="wide"
)

# ---------------- ESTADO DE SESSÃO ----------------
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "registro"

if "usuario" not in st.session_state:
    st.session_state["usuario"] = None


def ir_para(pagina: str):
    st.session_state["pagina"] = pagina


# ---------------- CSS BÁSICO DARK ----------------
st.markdown("""
<style>
body { background-color: #0E1117; color: white; }
.metric-card {
    background-color: #161B22;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("Experimento\nTanque de Água")

    if st.session_state["usuario"] is None:
        escolha = st.radio(
            "Menu",
            ["Cadastro", "Login"],
            index=0 if st.session_state["pagina"] == "registro" else 1
        )
        if escolha == "Cadastro":
            ir_para("registro")
        else:
            ir_para("login")
    else:
        escolha = st.radio(
            "Menu",
            ["Experimento", "Resultados"],
            index=0 if st.session_state["pagina"] == "experimento" else 1
        )
        if escolha == "Experimento":
            ir_para("experimento")
        else:
            ir_para("resultados")

        st.markdown("---")
        st.caption(f"Logado como **{st.session_state['usuario'].nome}**")
        if st.button("Sair"):
            st.session_state["usuario"] = None
            ir_para("login")

st.divider()

# ---------------- TELAS ----------------
def tela_registro():
    st.markdown("<h1 style='text-align:center;'>Cadastro</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; color:gray;'>Crie sua conta para acessar o experimento</p>",
        unsafe_allow_html=True
    )

    tipo = st.radio("Tipo de usuário", ["Aluno", "Professor"], horizontal=True)
    nome = st.text_input("Nome")
    email = st.text_input("E-mail")

    if st.button("Cadastrar"):
        if not nome or not email:
            st.error("Preencha nome e e-mail.")
        else:
            usuario = service.cadastrar_usuario(nome, email, tipo)  # type: ignore[arg-type]
            st.session_state["usuario"] = usuario
            st.success("Cadastro realizado com sucesso!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Ir para o experimento"):
                    ir_para("experimento")
            with col2:
                if st.button("Ver resultados"):
                    ir_para("resultados")


def tela_login():
    st.markdown("<h1 style='text-align:center;'>Login</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; color:gray;'>Entre com seu e-mail cadastrado</p>",
        unsafe_allow_html=True
    )

    email = st.text_input("E-mail")
    nome = st.text_input("Nome (caso ainda não tenha cadastro)")

    if st.button("Entrar"):
        if not email:
            st.error("Informe o e-mail.")
        else:
            usuario = service.login(email, nome)
            st.session_state["usuario"] = usuario
            st.success("Login realizado!")
            ir_para("experimento")


def tela_experimento():
    usuario = st.session_state["usuario"]
    if usuario is None:
        st.warning("Faça login ou cadastro antes de acessar o experimento.")
        return

    st.markdown(
        "<h1 style='text-align:center;'>💧 Experimento do Tanque de Água</h1>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='text-align:center; color:gray;'>Painel de análise do experimento</p>",
        unsafe_allow_html=True
    )

    st.divider()

    st.sidebar.subheader("Parâmetros do Experimento")
    tempo_total = st.sidebar.slider("Tempo (s)", 10, 200, 100)
    vazao_entrada = st.sidebar.number_input("Vazão de entrada (L/s)", value=5.0)
    vazao_saida = st.sidebar.number_input("Vazão de saída (L/s)", value=3.0)
    altura_max = st.sidebar.number_input("Altura máxima (m)", value=10.0)
    executar = st.sidebar.button("Executar Simulação")

    if executar:
        res = service.rodar_experimento(
            email_usuario=usuario.email,
            tempo_total=tempo_total,
            vazao_entrada=vazao_entrada,
            vazao_saida=vazao_saida,
            altura_max=altura_max,
        )
    else:
        res = service.obter_ultimo_resultado(usuario.email)

    # se ainda não tiver resultado, só mostra info
    if res is None:
        st.info("Clique em 'Executar Simulação' na barra lateral para gerar os resultados.")
        return

    # métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"<div class='metric-card'><h3>Altura Máxima</h3><h1>{res.altura_maxima:.2f} m</h1></div>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"<div class='metric-card'><h3>Erro Médio</h3><h1>{res.erro_medio:.2f}</h1></div>",
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"<div class='metric-card'><h3>Tempo Total</h3><h1>{res.tempo_total} s</h1></div>",
            unsafe_allow_html=True
        )

    st.divider()

    # gráficos
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("Evolução do Nível do Tanque")
        fig, ax = plt.subplots()
        ax.plot(res.tempo, res.nivel_aluno, label="Aluno")
        ax.plot(res.tempo, res.nivel_ideal, label="Ideal", linestyle="--")
        ax.set_xlabel("Tempo (s)")
        ax.set_ylabel("Nível (m)")
        ax.legend()
        st.pyplot(fig)

    with col_g2:
        st.subheader("Comparação")
        fig2, ax2 = plt.subplots()
        ax2.plot(res.tempo, res.nivel_aluno - res.nivel_ideal, label="Erro")
        ax2.set_xlabel("Tempo (s)")
        ax2.set_ylabel("Diferença (m)")
        ax2.legend()
        st.pyplot(fig2)


def tela_resultados():
    usuario = st.session_state["usuario"]
    if usuario is None:
        st.warning("Faça login ou cadastro antes de ver os resultados.")
        return

    # pega o último experimento desse usuário
    res = service.obter_ultimo_resultado(usuario.email)

    st.markdown(
        "<h1 style='text-align:center;'>Resultados do Experimento</h1>",
        unsafe_allow_html=True,
    )

    if res is None:
        st.markdown(
            "<p style='text-align:center; color:gray;'>Nenhuma simulação foi executada ainda.</p>",
            unsafe_allow_html=True,
        )
        return

    # cards individuais
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Altura máxima (m)", f"{res.altura_maxima:.2f}")
    with col2:
        st.metric("Erro médio", f"{res.erro_medio:.4f}")
    with col3:
        st.metric("Tempo total (s)", f"{res.tempo_total}")

    st.divider()

    # TABELA RESUMO (uma linha para o usuário logado)
    st.subheader("Resultados em tabela")

    df_resumo = pd.DataFrame(
        [
            {
                "Nome do usuário": usuario.nome,
                "Altura máxima (m)": res.altura_maxima,
                "Erro médio": res.erro_medio,
                "Tempo total (s)": res.tempo_total,
            }
        ]
    )

    st.dataframe(df_resumo)

# ---------------- ROTEAMENTO ----------------
pagina = st.session_state["pagina"]

if pagina == "registro":
    tela_registro()
elif pagina == "login":
    tela_login()
elif pagina == "experimento":
    tela_experimento()
elif pagina == "resultados":
    tela_resultados()
