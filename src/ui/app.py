import hashlib
import re
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from src.agent.loop import run_agent
from src.agent.graph import run_agent_langgraph
from src.data.user_datasets import load_uploaded_files
from src.tools.sql_tools import get_table_schemas, set_active_dataset


st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
    div[data-testid="stChatMessage"] { display: flex; }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"]) {
        flex-direction: row-reverse;
        text-align: right;
        justify-content: flex-start;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarUser"])
        div[data-testid="stChatMessageContent"] {
        text-align: right;
        background-color: rgba(255, 75, 75, 0.10);
        border-radius: 12px;
        padding: 10px 14px;
        max-width: 50%;
        margin-left: auto;
        margin-right: 0;
    }
    div[data-testid="stChatMessage"]:has(div[data-testid="stChatMessageAvatarAssistant"])
        div[data-testid="stChatMessageContent"] {
        max-width: 75%;
    }
</style>
""", unsafe_allow_html=True)

context = get_script_run_ctx(suppress_warning=True)
if context is None:
    raise RuntimeError("L'interface doit être lancée avec Streamlit.")
session_id = context.session_id

for key, value in (
    ("chat_messages", []),
    ("agent_history", []),
    ("show_trace", False),
    ("engine", "LangGraph"),
    ("uploaded_connection", None),
    ("uploaded_tables", []),
    ("upload_signature", None),
    ("upload_error", None),
    ("dataset_choice", "Données de démonstration"),
    ("active_source", "Données de démonstration"),
):
    if key not in st.session_state:
        st.session_state[key] = value


def clear_conversation() -> None:
    st.session_state.chat_messages = []
    st.session_state.agent_history = []


def strip_image_links(text: str) -> str:
    return re.sub(r"!\[.*?\]\((.*?)\)", "", text).strip()


def stream_text(placeholder, text: str, delay: float = 0.005) -> None:
    displayed = ""
    for char in text:
        displayed += char
        placeholder.markdown(displayed + "▌")
        time.sleep(delay)
    placeholder.markdown(displayed)


def run_agent_dispatch(question: str, history: list):
    if st.session_state.engine == "LangGraph":
        return run_agent_langgraph(question, history=history, verbose=False)
    return run_agent(question, history=history, verbose=False)


def suggested_questions(
    schemas: list[tuple[str, list[tuple[str, str]]]],
) -> list[str]:
    if not schemas:
        return []

    table_name, columns = schemas[0]
    questions = [f"Combien de lignes contient la table « {table_name} » ?"]
    numeric = [
        name for name, kind in columns
        if any(token in kind.upper() for token in ("INT", "REAL", "FLOAT", "DOUBLE", "DECIMAL"))
    ]
    categorical = [
        name for name, kind in columns
        if any(token in kind.upper() for token in ("VARCHAR", "TEXT", "STRING"))
    ]
    dates = [
        name for name, kind in columns
        if "DATE" in kind.upper() or "TIME" in kind.upper()
    ]

    if numeric:
        questions.append(
            f"Quel est le total et la moyenne de « {numeric[0]} » dans « {table_name} » ?"
        )
    if numeric and categorical:
        questions.append(
            f"Compare le total de « {numeric[0]} » par « {categorical[0]} » "
            f"dans « {table_name} »."
        )
    if dates and numeric:
        questions.append(
            f"Comment évolue « {numeric[0]} » au fil du temps selon « {dates[0]} » ?"
        )
    elif categorical:
        questions.append(
            f"Quelles sont les cinq valeurs les plus fréquentes de « {categorical[0]} » "
            f"dans « {table_name} » ?"
        )
    return questions[:4]


st.caption("Bonjour ! Chargez vos données ou utilisez le jeu de démonstration, puis posez vos questions.")

with st.sidebar:
    st.title("📊 AI Data Analyst Agent")
    st.header("📂 Dataset")

    uploaded_files = st.file_uploader(
        "Charger des fichiers CSV, Excel (.xlsx) ou JSON",
        type=["csv", "xlsx", "json"],
        accept_multiple_files=True,
        help=(
            "Chaque fichier devient une table. Chaque feuille d'un fichier Excel "
            "est importée séparément. Les fichiers restent en mémoire pendant la session."
        ),
        key="dataset_upload",
    )

    upload_signature = None
    if uploaded_files:
        digest = hashlib.sha256()
        for uploaded_file in uploaded_files:
            digest.update(uploaded_file.name.encode("utf-8"))
            digest.update(uploaded_file.getvalue())
        upload_signature = digest.hexdigest()

    if upload_signature != st.session_state.upload_signature:
        previous_connection = st.session_state.uploaded_connection
        set_active_dataset(session_id, None)
        if previous_connection is not None:
            previous_connection.close()
        st.session_state.uploaded_connection = None
        st.session_state.uploaded_tables = []
        st.session_state.upload_error = None
        st.session_state.upload_signature = upload_signature

        if uploaded_files:
            try:
                connection, table_details = load_uploaded_files(uploaded_files)
            except ValueError as error:
                st.session_state.upload_error = str(error)
            else:
                st.session_state.uploaded_connection = connection
                st.session_state.uploaded_tables = table_details
                st.session_state.dataset_choice = "Mon dataset"

        clear_conversation()

    if st.session_state.upload_error:
        st.error(st.session_state.upload_error)

    dataset_options = ["Données de démonstration"]
    if st.session_state.uploaded_connection is not None:
        dataset_options.append("Mon dataset")
    if st.session_state.dataset_choice not in dataset_options:
        st.session_state.dataset_choice = dataset_options[0]

    selected_source = st.radio(
        "Données à interroger",
        options=dataset_options,
        key="dataset_choice",
        help="Le fichier importé est temporaire et ne modifie pas la base de démonstration.",
    )
    if selected_source != st.session_state.active_source:
        clear_conversation()
        st.session_state.active_source = selected_source

    active_connection = (
        st.session_state.uploaded_connection if selected_source == "Mon dataset" else None
    )
    set_active_dataset(session_id, active_connection)
    if active_connection is not None:
        st.success(f"{len(st.session_state.uploaded_tables)} table(s) importée(s).")
        for table_name, row_count, _ in st.session_state.uploaded_tables:
            st.caption(f"`{table_name}` · {row_count:,} ligne(s)")

    st.header("⚙️ Options")
    st.session_state.engine = st.radio(
        "🧠 Moteur d'agent",
        options=["LangGraph", "Manuel"],
        index=0 if st.session_state.engine == "LangGraph" else 1,
        help=(
            "**LangGraph** : orchestration avec un graphe d'étapes.\n\n"
            "**Manuel** : boucle d'agent codée directement en Python."
        ),
    )
    st.session_state.show_trace = st.toggle(
        "Afficher les outils appelés", value=st.session_state.show_trace
    )

    if st.button("🗑️ Nouvelle conversation", use_container_width=True):
        clear_conversation()

schemas = get_table_schemas()
with st.expander("🔎 Explorer les tables et colonnes", expanded=False):
    if schemas:
        for table_name, columns in schemas:
            st.markdown(f"**{table_name}**")
            st.caption(" · ".join(f"{name} ({kind})" for name, kind in columns))
    else:
        st.info("Aucune table trouvée dans le dataset sélectionné.")

st.markdown("### 💡 Pour commencer, essayez une question")
suggestions = suggested_questions(schemas)
if suggestions:
    for start in range(0, len(suggestions), 2):
        columns = st.columns(2)
        for column, question in zip(columns, suggestions[start:start + 2]):
            if column.button(question, use_container_width=True, key=f"suggestion_{start}_{question}"):
                st.session_state.pending_question = question
else:
    st.info("Chargez un dataset tabulaire pour découvrir des exemples de questions.")

for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        for img_path in msg.get("images", []):
            image_path = Path(img_path)
            if image_path.exists():
                st.image(str(image_path), use_container_width=True)

prompt = st.chat_input("Posez votre question sur les données...")
if not prompt:
    prompt = st.session_state.pop("pending_question", None)

if prompt:
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyse des données en cours..."):
            result = run_agent_dispatch(prompt, st.session_state.agent_history)

        clean_text = strip_image_links(result["answer"])
        stream_text(st.empty(), clean_text)

        artifacts = result.get("artifacts", [])
        for img_path in artifacts:
            image_path = Path(img_path)
            if image_path.exists():
                st.image(str(image_path), use_container_width=True)
            else:
                st.warning(f"Image introuvable : {img_path}")

        if st.session_state.show_trace:
            with st.expander("🔍 Outils appelés", expanded=False):
                for message in result["messages"]:
                    if isinstance(message, dict):
                        if message.get("role") == "assistant" and message.get("tool_calls"):
                            for tool_call in message["tool_calls"]:
                                st.code(
                                    f"{tool_call['function']['name']}"
                                    f"({tool_call['function']['arguments']})",
                                    language="json",
                                )
                    elif getattr(message, "tool_calls", None):
                        for tool_call in message.tool_calls:
                            st.code(f"{tool_call['name']}({tool_call['args']})")

    st.session_state.chat_messages.append({
        "role": "assistant",
        "content": clean_text,
        "images": artifacts,
    })
    st.session_state.agent_history = result["history"]
