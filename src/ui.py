"""
Módulo de interfaz de usuario para UNSPSC DGCP
Integración con DIGEPRES desde catalogo_final.csv
"""

import streamlit as st
import pandas as pd
from typing import List, Tuple, Optional
from datetime import datetime
from src.config import get_config
from src.database import DatabaseManager
from src.models import EmbeddingManager
from src.search import SearchEngine
from src.utils import normalizar
from src.export import generar_excel
from src.digepres_integration import DigepresIntegration

class UIManager:
    """Gestor de la interfaz de usuario"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.embedding_manager = EmbeddingManager()
        self.config = get_config()
        self.digepres = DigepresIntegration()
        self._init_session_state()
    
    def _init_session_state(self):
        """Inicializa el estado de sesión de Streamlit"""
        if "limpiar" not in st.session_state:
            st.session_state.limpiar = False
        if "consulta" not in st.session_state:
            st.session_state.consulta = ""
        if "resultados_mostrados" not in st.session_state:
            st.session_state.resultados_mostrados = False
        if "ultima_busqueda" not in st.session_state:
            st.session_state.ultima_busqueda = ""
        if "ejecutar_busqueda" not in st.session_state:
            st.session_state.ejecutar_busqueda = False
    
    def render(self):
        """Renderiza la interfaz completa"""
        self._render_configuracion()
        self._render_cabecera()
        
        with st.spinner("Cargando catálogo..."):
            catalogo = self.db_manager.cargar_catalogo()
            sinonimos = self.db_manager.cargar_sinonimos()
            equivalencias = self.db_manager.cargar_equivalencias_digepres()
            
            with st.spinner("Cargando embeddings..."):
                embeddings = self.embedding_manager.cargar_embeddings()
        
        catalogo_filtrado = self._render_filtros(catalogo)
        consulta = self._render_busqueda()
        
        # Ejecutar búsqueda solo si hay consulta y no se ha limpiado
        if consulta and st.session_state.ejecutar_busqueda:
            self._ejecutar_busqueda(consulta, catalogo_filtrado, embeddings, sinonimos, equivalencias)
            st.session_state.ejecutar_busqueda = False
        elif consulta and st.session_state.consulta != "" and not st.session_state.get("limpiar_click", False):
            self._ejecutar_busqueda(consulta, catalogo_filtrado, embeddings, sinonimos, equivalencias)
    
    def _render_configuracion(self):
        """Renderiza la configuración en la barra lateral"""
        # Mostrar estadísticas DIGEPRES en la barra lateral
        with st.sidebar.expander("📊 Estadísticas DIGEPRES", expanded=True):
            stats = self.digepres.obtener_estadisticas()
            st.metric("📦 Total ítems", stats['total'])
            st.metric("✅ Con DIGEPRES", stats['con_digepres'])
            st.metric("⚠️ Sin DIGEPRES", stats['sin_digepres'])
            st.metric("🏛️ Cuentas únicas", stats['cuentas_unicas'])
        
        with st.sidebar.expander("⚙️ Configuración avanzada", expanded=False):
            st.slider(
                "Score mínimo",
                min_value=0,
                max_value=100,
                value=self.config['MIN_SCORE'],
                key="min_score"
            )
            st.slider(
                "Resultados máximos",
                min_value=5,
                max_value=50,
                value=self.config['MAX_RESULTS'],
                key="max_results"
            )
    
    def _render_cabecera(self):
        """Renderiza la cabecera de la aplicación"""
        st.markdown(
            """
            <h1 style='text-align: center; color: #1a5276; font-size: 28px; margin-bottom: 5px;'>
                🔎 BUSCADOR CATÁLOGO DE BIENES/SERVICIOS DGCP
            </h1>
            <hr style='border: 2px solid #1a5276; margin-top: 5px; margin-bottom: 20px;'>
            """,
            unsafe_allow_html=True
        )
    
    def _render_filtros(self, catalogo: pd.DataFrame) -> pd.DataFrame:
        """Renderiza los filtros de búsqueda"""
        st.sidebar.header("Filtros")
        
        if catalogo.empty:
            return catalogo
        
        segmentos = sorted(catalogo["Segmento"].dropna().unique())
        segmento = st.sidebar.selectbox("Segmento", ["Todos"] + list(segmentos), key="segmento")
        
        if segmento != "Todos":
            catalogo_filtrado = catalogo[catalogo["Segmento"] == segmento]
        else:
            catalogo_filtrado = catalogo
        
        if not catalogo_filtrado.empty:
            familias = sorted(catalogo_filtrado["Familia"].dropna().unique())
            familia = st.sidebar.selectbox("Familia", ["Todas"] + list(familias), key="familia")
            
            if familia != "Todas":
                catalogo_filtrado = catalogo_filtrado[catalogo_filtrado["Familia"] == familia]
            
            if not catalogo_filtrado.empty:
                clases = sorted(catalogo_filtrado["Clase"].dropna().unique())
                clase = st.sidebar.selectbox("Clase", ["Todas"] + list(clases), key="clase")
                
                if clase != "Todas":
                    catalogo_filtrado = catalogo_filtrado[catalogo_filtrado["Clase"] == clase]
        
        return catalogo_filtrado
    
    def _render_busqueda(self) -> str:
        """Renderiza la barra de búsqueda"""
        col1, col2 = st.columns([4, 1])
        
        with col1:
            consulta = st.text_input(
                "**Describa el bien o servicio:**",
                value=st.session_state.consulta,
                key="consulta_input",
                placeholder="Ejemplo: Compuestos endurecedores mortuorios"
            )
        
        with col2:
            st.write("")
            st.write("")
            if st.button("🧹 Limpiar", use_container_width=True, type="primary"):
                st.session_state.consulta = ""
                st.session_state.resultados_mostrados = False
                st.session_state.ultima_busqueda = ""
                st.session_state.ejecutar_busqueda = False
                st.session_state.limpiar_click = True
                st.rerun()
        
        # Si el usuario escribió algo nuevo, activar búsqueda
        if consulta != st.session_state.consulta:
            st.session_state.consulta = consulta
            if consulta:
                st.session_state.ejecutar_busqueda = True
                st.session_state.limpiar_click = False
        
        return consulta
    
    def _ejecutar_busqueda(self, consulta: str, catalogo_filtrado: pd.DataFrame, 
                          embeddings: pd.DataFrame, sinonimos: dict, equivalencias: pd.DataFrame):
        """Ejecuta la búsqueda y muestra los resultados"""
        import time
        inicio = time.time()
        
        consulta_norm = normalizar(consulta)
        relacionados_info = sinonimos.get(consulta_norm, [])
        sinonimos_lista = [t for t, _ in relacionados_info]
        
        if sinonimos_lista:
            st.info(f"🔗 Términos relacionados: {', '.join(sinonimos_lista)}")
        
        search_engine = SearchEngine(catalogo_filtrado, embeddings)
        resultados = search_engine.buscar(consulta, sinonimos_lista)
        
        self.db_manager.registrar_consulta(consulta, len(resultados))
        
        tiempo = round(time.time() - inicio, 2)
        
        # Mostrar métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("📊 Resultados", len(resultados))
        col2.metric("🔗 Sinónimos", len(sinonimos_lista))
        col3.metric("⏱️ Tiempo (s)", tiempo)
        
        # Preparar exportación
        df_exportar = self._preparar_exportacion(resultados)
        
        if not df_exportar.empty:
            self._render_boton_exportar(df_exportar)
        
        self._mostrar_resultados(resultados, equivalencias)
        
        # Marcar que ya se mostraron resultados
        st.session_state.resultados_mostrados = True
        st.session_state.ultima_busqueda = consulta
    
    def _preparar_exportacion(self, resultados: List) -> pd.DataFrame:
        """Prepara los datos para exportación"""
        exportar = []
        for score, exacto, fila in resultados:
            codigo = fila.get("Código UNSPSC", "")
            # Obtener DIGEPRES para exportación
            cuenta_digepres, descripcion_digepres = self.digepres.obtener_cuenta(codigo)
            
            exportar.append({
                "Tipo": "Exacta" if exacto else "Relacionada",
                "Score": round(score, 2),
                "Código UNSPSC": codigo,
                "Descripción": fila.get("Descripción", ""),
                "Definición": fila.get("Definición", ""),
                "Segmento": fila.get("Segmento", ""),
                "Familia": fila.get("Familia", ""),
                "Clase": fila.get("Clase", ""),
                "Cuenta DIGEPRES": cuenta_digepres or "Sin asignar",
                "Descripción DIGEPRES": descripcion_digepres or ""
            })
        return pd.DataFrame(exportar)
    
    def _render_boton_exportar(self, df_exportar: pd.DataFrame):
        """Renderiza el botón de exportación"""
        archivo = generar_excel(df_exportar)
        st.download_button(
            "📥 Exportar Excel",
            archivo,
            file_name=f"resultados_unspsc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    def _mostrar_resultados(self, resultados: List, equivalencias: pd.DataFrame):
        """Muestra los resultados en la interfaz con DIGEPRES integrado"""
        if not resultados:
            st.warning("No se encontraron resultados para esta búsqueda.")
            return
        
        # Crear DataFrame con resultados y DIGEPRES
        datos = []
        for score, exacto, fila in resultados:
            codigo = fila.get('Código UNSPSC', '')
            
            # Obtener DIGEPRES desde el CSV integrado
            cuenta_digepres = None
            descripcion_digepres = None
            
            try:
                cuenta, desc = self.digepres.obtener_cuenta(codigo)
                if cuenta:
                    cuenta_digepres = cuenta
                    descripcion_digepres = desc
            except:
                pass
            
            # Fallback a la base de datos si no se encuentra en el CSV
            if not cuenta_digepres:
                try:
                    resultado_db = self.db_manager.obtener_imputacion_presupuestaria(str(codigo))
                    if resultado_db and len(resultado_db) > 3:
                        cuenta_digepres = resultado_db[3]
                        descripcion_digepres = resultado_db[4] if len(resultado_db) > 4 else ""
                except:
                    pass
            
            # Fallback a equivalencias
            if not cuenta_digepres:
                try:
                    codigo_familia = fila.get("Código Familia", "")
                    if codigo_familia:
                        eq_resultado = equivalencias[equivalencias["codigo_familia"].astype(str) == str(codigo_familia)]
                        if not eq_resultado.empty:
                            cuenta_digepres = eq_resultado.iloc[0].get("cuenta_digepres", "")
                            descripcion_digepres = eq_resultado.iloc[0].get("descripcion_digepres", "")
                except:
                    pass
            
            datos.append({
                'Score': round(score, 2),
                'Exacto': '✅' if exacto else '🔄',
                'Código UNSPSC': codigo,
                'Descripción': fila.get('Descripción', ''),
                'Familia': fila.get('Familia', ''),
                'Segmento': fila.get('Segmento', ''),
                'Cuenta DIGEPRES': cuenta_digepres or '⚠️ Sin asignar',
                'Descripción DIGEPRES': descripcion_digepres or ''
            })
        
        df_resultados = pd.DataFrame(datos)
        
        st.subheader(f"📋 Resultados encontrados: {len(resultados)}")
        
        # Mostrar tabla principal con DIGEPRES
        st.dataframe(
            df_resultados[['Score', 'Exacto', 'Código UNSPSC', 'Descripción', 'Cuenta DIGEPRES', 'Descripción DIGEPRES']],
            use_container_width=True,
            height=400,
            column_config={
                "Score": st.column_config.NumberColumn("Score", format="%.0f%%"),
                "Exacto": st.column_config.TextColumn("Exacta", width="small"),
                "Código UNSPSC": st.column_config.TextColumn("Código", width="small"),
                "Descripción": st.column_config.TextColumn("Descripción", width="medium"),
                "Cuenta DIGEPRES": st.column_config.TextColumn("Cuenta DIGEPRES", width="small"),
                "Descripción DIGEPRES": st.column_config.TextColumn("Descripción DIGEPRES", width="large"),
            }
        )
        
        # Mostrar detalle expandible con información completa
        st.markdown("---")
        st.caption("📌 Haz clic en cada resultado para ver detalles completos")
        
        for i, row in df_resultados.iterrows():
            with st.expander(f"📌 {row['Código UNSPSC']} - {row['Descripción']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**📋 Datos del Producto**")
                    st.write(f"**Código:** {row['Código UNSPSC']}")
                    st.write(f"**Descripción:** {row['Descripción']}")
                    st.write(f"**Familia:** {row['Familia']}")
                    st.write(f"**Segmento:** {row['Segmento']}")
                    st.write(f"**Score:** {row['Score']:.0f}%")
                    st.write(f"**Coincidencia:** {'Exacta' if row['Exacto'] == '✅' else 'Relacionada'}")
                with col2:
                    st.markdown("**💰 Clasificación DIGEPRES**")
                    if row['Cuenta DIGEPRES'] != '⚠️ Sin asignar':
                        st.write(f"**Cuenta:** {row['Cuenta DIGEPRES']}")
                        st.write(f"**Denominación:** {row['Descripción DIGEPRES']}")
                    else:
                        st.warning("⚠️ No se encontró cuenta DIGEPRES para este código")
                        st.info("💡 Si conoces la cuenta, puedes agregarla manualmente al archivo mapeo_completo.xlsx")
    
    def _mostrar_resultado_individual(self, score: float, fila: pd.Series, equivalencias: pd.DataFrame):
        """Muestra un resultado individual con DIGEPRES desde catalogo_final.csv"""
        codigo_unspsc = fila.get('Código UNSPSC', '')
        
        # Buscar directamente en el CSV integrado
        cuenta_digepres = None
        denominacion_digepres = None
        
        try:
            cuenta, desc = self.digepres.obtener_cuenta(codigo_unspsc)
            if cuenta:
                cuenta_digepres = cuenta
                denominacion_digepres = desc
        except:
            pass
        
        # Fallback a la base de datos si no se encuentra en el CSV
        if not cuenta_digepres:
            try:
                resultado_db = self.db_manager.obtener_imputacion_presupuestaria(str(codigo_unspsc))
                if resultado_db and len(resultado_db) > 3:
                    cuenta_digepres = resultado_db[3]
                    denominacion_digepres = resultado_db[4] if len(resultado_db) > 4 else ""
            except:
                pass
        
        # Fallback a equivalencias
        if not cuenta_digepres:
            try:
                codigo_familia = fila.get("Código Familia", "")
                if codigo_familia:
                    eq_resultado = equivalencias[equivalencias["codigo_familia"].astype(str) == str(codigo_familia)]
                    if not eq_resultado.empty:
                        cuenta_digepres = eq_resultado.iloc[0].get("cuenta_digepres", "")
                        denominacion_digepres = eq_resultado.iloc[0].get("descripcion_digepres", "")
            except:
                pass
        
        with st.expander(
            f"{score:.0f}% | {fila.get('Código UNSPSC', '')} | {fila.get('Descripción', '')}"
        ):
            cols = st.columns(2)
            
            with cols[0]:
                st.markdown("**📌 Datos del Producto**")
                st.write("**Código UNSPSC:**", fila.get("Código UNSPSC", ""))
                st.write("**Descripción:**", fila.get("Descripción", ""))
                st.write("**Segmento:**", fila.get("Segmento", ""))
                st.write("**Familia:**", fila.get("Familia", ""))
                st.write("**Clase:**", fila.get("Clase", ""))
            
            with cols[1]:
                st.markdown("**📖 Definición**")
                st.write(fila.get("Definición", "No disponible"))
                
                st.markdown("---")
                st.markdown("**💰 Cuenta DIGEPRES**")
                if cuenta_digepres:
                    st.write("**Cuenta:**", cuenta_digepres)
                    st.write("**Denominación:**", denominacion_digepres or "No disponible")
                else:
                    st.warning("⚠️ No se encontró cuenta DIGEPRES para este código")
                    st.info("💡 Si conoces la cuenta, puedes agregarla manualmente al archivo mapeo_completo.xlsx")
    
    def _obtener_imputacion_presupuestaria(self, codigo_unspsc: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Obtiene la imputación presupuestaria desde la tabla imputaciones_presupuestarias"""
        try:
            db = DatabaseManager()
            resultado = db.obtener_imputacion_presupuestaria(codigo_unspsc)
            
            if resultado:
                auxiliar = resultado[3] if len(resultado) > 3 else None
                denominacion = resultado[4] if len(resultado) > 4 else None
                definicion = resultado[2] if len(resultado) > 2 else None
                return auxiliar, denominacion, definicion
            
            return None, None, None
            
        except Exception as e:
            print(f"Error al obtener imputación: {e}")
            return None, None, None
    
    def _obtener_digepres_equivalencia(self, fila: pd.Series, equivalencias: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
        """Obtiene la clasificación DIGEPRES desde equivalencias (fallback)"""
        try:
            codigo_familia = fila.get("Código Familia", "")
            if codigo_familia:
                resultado = equivalencias[equivalencias["codigo_familia"].astype(str) == str(codigo_familia)]
                if not resultado.empty:
                    return resultado.iloc[0]["cuenta_digepres"], resultado.iloc[0]["descripcion_digepres"]
        except:
            pass
        
        return None, None