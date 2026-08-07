# =====================================================
# SIDEBAR - LOGO + FILTROS
# =====================================================
with st.sidebar:
    # =====================================================
    # LOGO CON FUNCIÓN DE INICIO (CLICKABLE)
    # =====================================================
    try:
        # URL del logo (usando el commit específico o main para la última versión)
        # Opción 1: Usar un commit específico (recomendado para estabilidad)
        logo_url = "https://raw.githubusercontent.com/cybersolushop-star/UNSPSC_DGCP_Expert/6df141cc0e6021de921153b1d343128bc6e35290/data/logo.png"
        
        # Opción 2: Usar siempre la última versión de main (descomentar para usar)
        # logo_url = "https://raw.githubusercontent.com/cybersolushop-star/UNSPSC_DGCP_Expert/main/data/logo.png"
        
        # Estilos CSS para el logo
        st.markdown("""
        <style>
            .sidebar-logo-container {
                text-align: center;
                padding: 5px 0 5px 0;
                border-bottom: 2px solid #334155;
                margin-bottom: 10px;
                cursor: pointer;
            }
            .sidebar-logo-wrapper {
                background: white;
                border-radius: 12px;
                padding: 6px;
                margin: 0 auto;
                max-width: 130px;
                box-shadow: 0 3px 5px rgba(0,0,0,0.25);
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .sidebar-logo-wrapper:hover {
                transform: scale(1.05);
                box-shadow: 0 6px 12px rgba(0,0,0,0.4);
            }
            .sidebar-logo-wrapper img {
                display: block;
                width: 100%;
                height: auto;
                border-radius: 6px;
            }
            .sidebar-logo-title {
                font-size: 0.75rem;
                color: #94a3b8;
                margin-top: 4px;
                transition: color 0.2s ease;
                cursor: pointer;
            }
            .sidebar-logo-title:hover {
                color: #e2e8f0;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Mostrar el logo con funcionalidad de clic
        st.markdown(f"""
        <div class="sidebar-logo-container" onclick="window.location.href = window.location.pathname + '?reset=true';">
            <div class="sidebar-logo-wrapper">
                <img src="{logo_url}" alt="Logo UNSPSC DGCP - Ir al inicio">
            </div>
            <div class="sidebar-logo-title">
                🏠 Buscador de Bienes y Servicios
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        # Fallback con emoji si el logo no se puede cargar
        st.markdown("""
        <div class="sidebar-logo-container" onclick="window.location.href = window.location.pathname + '?reset=true';">
            <div style="
                background: linear-gradient(135deg, #1a5276, #154360);
                border-radius: 12px;
                padding: 12px;
                margin: 0 auto;
                max-width: 130px;
                box-shadow: 0 3px 5px rgba(0,0,0,0.25);
                cursor: pointer;
                transition: transform 0.2s ease;
            ">
                <div style="font-size: 3rem; margin: 0;">🔎</div>
                <div style="
                    font-size: 0.85rem;
                    font-weight: 700;
                    color: white;
                    margin: 3px 0 2px 0;
                ">
                    UNSPSC DGCP
                </div>
            </div>
            <div class="sidebar-logo-title" style="font-size: 0.75rem; color: #94a3b8; margin-top: 4px; cursor: pointer;">
                🏠 Buscador de Bienes y Servicios
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    st.header("📂 Filtros")
    
    try:
        df_catalogo = cargar_catalogo()
        
        if df_catalogo is not None and not df_catalogo.empty:
            segmentos = sorted(df_catalogo["Segmento"].dropna().unique())
            segmento = st.selectbox("Segmento", ["Todos"] + list(segmentos))
            
            if segmento != "Todos":
                df_filtrado = df_catalogo[df_catalogo["Segmento"] == segmento]
            else:
                df_filtrado = df_catalogo
            
            familias = sorted(df_filtrado["Familia"].dropna().unique())
            familia = st.selectbox("Familia", ["Todas"] + list(familias))
            
            if familia != "Todas":
                df_filtrado = df_filtrado[df_filtrado["Familia"] == familia]
            
            clases = sorted(df_filtrado["Clase"].dropna().unique())
            clase = st.selectbox("Clase", ["Todas"] + list(clases))
            
            if clase != "Todas":
                df_filtrado = df_filtrado[df_filtrado["Clase"] == clase]
            
            st.caption(f"📊 {len(df_filtrado)} ítems disponibles")
            st.session_state.df_filtrado = df_filtrado
        else:
            st.warning("No se pudo cargar el catálogo")
            st.session_state.df_filtrado = pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error cargando filtros: {e}")
        st.session_state.df_filtrado = pd.DataFrame()
    
    st.divider()
    if st.button("🧹 Limpiar Búsqueda", use_container_width=True):
        st.session_state.consulta = ""
        st.session_state.resultados = []
        st.session_state.sinonimos = []
        st.session_state.tipo_busqueda = "texto"
        st.session_state.pagina_actual = 1
        st.session_state.ultima_busqueda = ""
        st.session_state.search_time_ms = 0
        st.session_state.consulta_input = ""
        st.rerun()
    
    st.divider()
    st.caption("🔎 UNSPSC DGCP Expert v2.0")