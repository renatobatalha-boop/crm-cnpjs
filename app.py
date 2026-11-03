/* ========================================================
       ESTILIZAÇÃO TOTAL DO MODAL / DIALOG (FUNDO ESCURO & PRETO)
       ======================================================== */

    /* 1. Fundo e texto principal da janela modal */
    div[role="dialog"],
    div[data-testid="stModal"] > div {
        background-color: #120422 !important;
        background-image: radial-gradient(circle at 50% 0%, #260a45 0%, #120422 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 18px !important;
    }

    /* Título do Modal e botão de fechar (X) */
    div[role="dialog"] h2,
    div[role="dialog"] [data-testid="stDialogHeader"] {
        color: #FFFFFF !important;
    }
    div[role="dialog"] button[aria-label="Close"] svg {
        fill: #FFFFFF !important;
    }

    /* 2. Labels, subtítulos e textos informativos dentro do modal */
    div[role="dialog"] label,
    div[role="dialog"] label p,
    div[role="dialog"] p,
    div[role="dialog"] span,
    div[role="dialog"] .stMarkdown {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* 3. Caixas de Seleção (Selectbox) no modal: FUNDO PRETO e LETRA BRANCA */
    div[role="dialog"] div[data-baseweb="select"],
    div[role="dialog"] div[data-baseweb="select"] > div,
    div[role="dialog"] div[data-baseweb="select"] [aria-expanded] {
        background-color: #000000 !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
    }
    div[role="dialog"] div[data-baseweb="select"] span {
        color: #FFFFFF !important;
    }
    div[role="dialog"] div[data-baseweb="select"] svg {
        fill: #FFFFFF !important;
    }

    /* 4. Caixas de Texto (TextArea e TextInput) no modal: FUNDO PRETO e LETRA BRANCA */
    div[role="dialog"] div[data-baseweb="textarea"],
    div[role="dialog"] div[data-baseweb="textarea"] textarea,
    div[role="dialog"] div[data-baseweb="base-input"],
    div[role="dialog"] div[data-baseweb="input"] input {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 10px !important;
    }

    div[role="dialog"] textarea::placeholder,
    div[role="dialog"] input::placeholder {
        color: rgba(255, 255, 255, 0.45) !important;
        -webkit-text-fill-color: rgba(255, 255, 255, 0.45) !important;
    }

    /* 5. Botões de link secundários (Google Maps e WhatsApp) */
    div[role="dialog"] a[data-testid="stLinkButton"],
    div[role="dialog"] .stButton button:not([kind="primary"]) {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
    }
