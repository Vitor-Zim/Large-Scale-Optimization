import streamlit as st
from codes.read_instance_regex import MPSParser
from codes.run_solver import LinprogSolver, HighsSolver
import tempfile
import os
import time
from codes.generate_output_file import generate_output_file

# Lista de métodos disponíveis
METHOD_OPTIONS = [
    "HiGHS",
    "Linprog",
    "Descida por Coordenada",
    "Gradiente Espelhado",
    "Otimização Local",
    "Otimização Global",
    "Azeótropos"
]

# Configurações do Streamlit
def main():
    st.set_page_config(page_title="Solver de PL", layout="centered")
    st.title("Solver de Programação Linear")
    
    if "file_path" not in st.session_state:
        st.session_state.file_path = None
    if "processing" not in st.session_state:
        st.session_state.processing = False
    
    uploaded_file = st.file_uploader("Escolha um arquivo MPS", type=["mps"])
    
    #Alterei dessa forma para salvar o arquivo com o nome original e não com o nome temporário para evitar confusões e facilitar a saída
    if uploaded_file is not None:
        upload_folder = "uploads"
        os.makedirs(upload_folder, exist_ok=True)

        # Salva o arquivo com o nome original
        file_path = os.path.join(upload_folder, uploaded_file.name)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.session_state.file_path = file_path
        st.session_state.original_filename = uploaded_file.name

        st.session_state.function_type = st.selectbox(
            "Selecione o tipo de função",
            ["Linear", "Quadrática"]
        )

        st.session_state.method_selected = st.selectbox(
            "Selecione o método de otimização",
            METHOD_OPTIONS
        )
        
        if st.button("Confirmar e Resolver"):
            st.session_state.page = "results"
            st.session_state.processing = True
            st.rerun()


def select_solver(file_path, method_name):
    if method_name == "HiGHS":
        return HighsSolver(file_path)
    elif method_name == "Linprog":
        return LinprogSolver(file_path)
    elif method_name == "Descida por Coordenada":
        # Implementar o solver de Descida por Coordenada
        return None
    elif method_name == "Gradiente Espelhado":
        # Implementar o solver de Gradiente Espelhado
        return None
    elif method_name == "Otimização Local":
        # Implementar o solver de Otimização Local
        return None
    elif method_name == "Otimização Global":
        # Implementar o solver de Otimização Global
        return None
    elif method_name == "Azeótropos":
        # Implementar o solver de Azeótropos
        return None
    else:
        return None
    

def results_page():
    st.set_page_config(page_title="Resultados", layout="centered")
    st.title("Resultados da Otimização")
    
    if "file_path" not in st.session_state or st.session_state.file_path is None:
        st.error("Nenhum arquivo foi enviado.")
        
        if st.button("Voltar para o início"):
            st.session_state.page = "main"
            st.rerun()
        
        return
    
    if st.session_state.processing:
        st.write("Processando a otimização...")
        progress_bar = st.progress(0)
        
        try:
            solver = select_solver(st.session_state.file_path, st.session_state.method_selected)
            
            for i in range(1, 101):
                time.sleep(0.02)  # Simula progresso
                progress_bar.progress(i)

            if solver:
                print(">>> Rodando solver...")

                solver.run()
                print(">>> Solver rodou. Pegando resultados...")

                results = solver.get_results()
                print(f">>> Resultado do solver: {results}")

                st.session_state.results = results
                st.session_state.processing = False
                st.rerun()
            else:
                st.error(f"Método '{st.session_state.method_selected}' ainda não implementado.")
                st.session_state.processing = False
                st.rerun()

        except Exception as e:
            st.error(f"Erro ao processar o arquivo MPS: {e}")
            st.session_state.processing = False
            st.rerun()
    
    else:
        results = st.session_state.get("results", None)
        
        if results:
            st.write(f"**Status:** {results['status']}")
            st.write(f"**Valor objetivo:** {results['objective_value']}")
            st.write(f"**Sucesso:** {results['success']}")
            st.write(f"**Número de iterações:** {results['iterations']}")
        
            # Preparar pasta de saída
            output_folder = "outputs"
            os.makedirs(output_folder, exist_ok=True)

            # Pegar o nome original do arquivo
            original_file_name = os.path.basename(st.session_state.file_path)
            original_file_name_without_extension = os.path.splitext(original_file_name)[0]

            # Pegar o nome do método escolhido
            method_name = st.session_state.method_selected

            # Gerar o novo nome no formato desejado
            problem_name = f"{method_name}_{original_file_name_without_extension}"

            # Preparar variáveis primais e preços duais
            primal_vars = []
            if "primal_solution" in results and "dual_prices" in results:
                for idx, (primal, dual) in enumerate(zip(results["primal_solution"], results["dual_prices"]), 1):
                    primal_vars.append((idx, primal, dual))

            # Preparar restrições (folgas e duais)
            dual_vars = []
            if "slacks" in results and "dual_solution" in results:
                for idx, (slack, dual) in enumerate(zip(results["slacks"], results["dual_solution"]), 1):
                    dual_vars.append((idx, slack, dual))

            # Gerar arquivo de saída
            output_path = generate_output_file(
                output_folder=output_folder,
                problem_name=problem_name,
                solver_results={
                    "valor_otimo_primal": results.get("objective_value", 0),
                    "iterations": results.get("iterations", 0),
                    "gap": results.get("gap", 0),
                    "valor_otimo_dual": results.get("objective_value", 0),
                    "viabilidade_primal": results.get("primal_feasibility", 0) if results.get("has_feasibility", False) else 0.0,
                    "viabilidade_dual": results.get("dual_feasibility", 0) if results.get("has_feasibility", False) else 0.0,
                    "tempo": results.get("runtime", 0),
                },
                primal_vars=primal_vars,
                dual_vars=dual_vars
            )

            st.success(f"Arquivo gerado com sucesso: {output_path}")
            
        else:
            st.error("Erro ao resolver o problema.")
    
    if st.button("Voltar para o início"):
        
        if os.path.exists(st.session_state.file_path):
            os.unlink(st.session_state.file_path)
        
        st.session_state.file_path = None
        st.session_state.results = None
        st.session_state.page = "main"
        st.rerun()

# Gerenciar navegação entre páginas
if "page" not in st.session_state:
    st.session_state.page = "main"

if st.session_state.page == "main":
    main()
else:
    results_page()