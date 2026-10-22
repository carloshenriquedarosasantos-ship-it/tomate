import tkinter as tk
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from tkinter import filedialog 
from PIL import Image, ImageTk,ImageOps
from tkinter import messagebox 
from io import BytesIO

#----------------------------------------------------------------------
#def
#Função de segmentação do tomate
def segment_tomato(image_bgr, sat_threshold=80):
    """
    Segmenta o maior objeto colorido da imagem.

    Retorna:
        hsv   : imagem HSV
        mask  : máscara binária do tomate
        bbox  : (x, y, w, h)
    """
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    mask = np.uint8(hsv[:, :, 1] > sat_threshold) * 255

    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (7, 7)
    )

    mask = cv2.morphologyEx(
        mask, cv2.MORPH_OPEN, kernel, iterations=1
    )

    mask = cv2.morphologyEx(
        mask, cv2.MORPH_CLOSE, kernel, iterations=2
    )

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)

    if num_labels <= 1:
        return hsv, np.zeros_like(mask), None

    largest_label = 1 + np.argmax(
        stats[1:, cv2.CC_STAT_AREA]
    )

    object_mask = np.uint8(labels == largest_label) * 255

    x = stats[largest_label, cv2.CC_STAT_LEFT]
    y = stats[largest_label, cv2.CC_STAT_TOP]
    w = stats[largest_label, cv2.CC_STAT_WIDTH]
    h = stats[largest_label, cv2.CC_STAT_HEIGHT]

    return hsv, object_mask, (x, y, w, h)
# 9. Classificação baseada na distribuição das cores

def classify_maturity(
    hsv, mask,
    green_range=(25, 55),
    orange_range=(10, 25),
    red_low=10,
    red_high=170
):
    """
    Calcula a distribuição de cores dentro da máscara do tomate
    e determina o estágio de maturação.
    """

    object_pixels = mask > 0
    H = hsv[:, :, 0]
    S = hsv[:, :, 1]

    valid = object_pixels & (S >= 80)
    total = np.count_nonzero(valid)

    if total == 0:
        return {
            "estagio": "Indeterminado",
            "verde_pct": 0.0,
            "laranja_pct": 0.0,
            "vermelho_pct": 0.0,
            "hue_medio": np.nan
        }

    green = valid & (H >= green_range[0]) & (H <= green_range[1])
    orange = valid & (H > orange_range[0]) & (H < orange_range[1])
    red = valid & ((H <= red_low) | (H >= red_high))

    green_pct = 100 * np.count_nonzero(green) / total
    orange_pct = 100 * np.count_nonzero(orange) / total
    red_pct = 100 * np.count_nonzero(red) / total
    hue_mean = float(np.mean(H[valid]))

    # Regra inicial derivada do comportamento observado no dataset
    if green_pct >= 60:
        stage = "Verde"
    elif red_pct >= 50:
        stage = "Maduro"
    elif orange_pct >= 50:
        stage = "Em maturação"
    else:
        percentages = {
            "Verde": green_pct,
            "Em maturação": orange_pct,
            "Maduro": red_pct
        }
        stage = max(percentages, key=percentages.get)

    return {
        "Estagio": stage,
        "Verde_pct": green_pct,
        "Laranja_pct": orange_pct,
        "Vermelho_pct": red_pct,
        "Hue_medio": hue_mean
    }


#dectetar tomatte
def detect_tomato(image_bgr):
    hsv, mask, bbox = segment_tomato(image_bgr)

    if bbox is None:
        return {
            "image": image_bgr.copy(),
            "mask": mask,
            "bbox": None,
            "estagio": "Tomate não detectado"
        }

    info = classify_maturity(hsv, mask)
    result = image_bgr.copy()

    x, y, w, h = bbox

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    cv2.drawContours(
        result, contours, -1, (255, 0, 0), 2
    )

    cv2.rectangle(
        result,
        (x, y),
        (x + w, y + h),
        (255, 0, 0),
        3
    )

    label = (
        f"{info['Estagio']} | "
        f"V:{info['Verde_pct']:.1f}% "
        f"L:{info['Laranja_pct']:.1f}% "
        f"R:{info['Vermelho_pct']:.1f}%"
    )

    cv2.rectangle(
        result,
        (x, max(0, y - 35)),
        (min(result.shape[1], x + 500), y),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        result,
        label,
        (x + 5, max(23, y - 10)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    return {
        "image": result,
        "mask": mask,
        "bbox": bbox,
        **info
    }
# função da prévia
def fazer_upload_nativo():
    caminho_arquivo = filedialog.askopenfilename(
        title="Selecione uma imagem JPG",
        filetypes=[("Imagens JPG", "*.jpg *.jpeg")]
    )

    if caminho_arquivo:
        imagem_pil = Image.open(caminho_arquivo)
        imagem_np = np.array(imagem_pil)
        imagem = cv2.cvtColor(imagem_np, cv2.COLOR_RGB2BGR)
        result = detect_tomato(imagem)
        imgem_resulta_rgb = cv2.cvtColor(result["image"], cv2.COLOR_BGR2RGB)
        
        img_pil_correta2 = Image.fromarray(imagem_np)
                
        # Pega automaticamente a largura e altura exata que você travou no seu quadrado cinza
        largura_alvo2 = container_imagem2.winfo_width()
        altura_alvo2 = container_imagem2.winfo_height()

        img_pil_correta = Image.fromarray(imgem_resulta_rgb)
        
        # Pega automaticamente a largura e altura exata que você travou no seu quadrado cinza
        largura_alvo = container_imagem.winfo_width()
        altura_alvo = container_imagem.winfo_height()
        
        # Garante um tamanho mínimo caso a função seja chamada antes da janela renderizar totalmente
        if largura_alvo <= 1: 
            largura_alvo, altura_alvo = 350, 250 
            largura_alvo2, altura_alvo2 = 350, 250
            
        # Ajusta a foto para preencher 100% do espaço disponível no quadrado cinza
        imagem_redimensionada = ImageOps.fit(img_pil_correta, (largura_alvo, altura_alvo), Image.Resampling.LANCZOS)
        imagem_redimensionada2 = ImageOps.fit(img_pil_correta2, (largura_alvo2, altura_alvo2), Image.Resampling.LANCZOS)

        imagem_tk = ImageTk.PhotoImage(imagem_redimensionada)#image resultado
        imagem_tk2 = ImageTk.PhotoImage(imagem_redimensionada2)#image original

        # === SOLUÇÃO: Remove os textos da tela para dar espaço exclusivo para as fotos ===
        texto_aviso2.grid_forget()
        texto_aviso.grid_forget()

        # Atualiza as labels exibindo apenas as fotos processadas
        label_imagem2.config(image=imagem_tk2)
        label_imagem2.image = imagem_tk2
        label_imagem.config(image=imagem_tk)
        label_imagem.image = imagem_tk
#area analise
        hsv, mask, bbox = segment_tomato(imagem)
        result = imagem.copy()

        if bbox is not None:
            x, y, w, h = bbox
            cv2.rectangle(result, (x, y), (x+w, y+h), (255, 0, 0), 3)

        img_pil_correta3 = Image.fromarray(imagem_np)
        largura_alvo3 = container_imagem3.winfo_width()
        altura_alvo3 = container_imagem3.winfo_height()

        img_pil_correta6 = Image.fromarray(imgem_resulta_rgb)
        largura_alvo6 = container_imagem6.winfo_width()
        altura_alvo6 = container_imagem6.winfo_height()

        img_pil_correta4 = Image.fromarray(mask)
        largura_alvo4 = container_imagem4.winfo_width()
        altura_alvo4 = container_imagem4.winfo_height()

        result2=cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        img_pil_correta5 = Image.fromarray(result2)
        largura_alvo5 = container_imagem5.winfo_width()
        altura_alvo5 = container_imagem5.winfo_height()


        if largura_alvo <= 1: 
            largura_alvo3, altura_alvo3 = 150, 100 
            largura_alvo6, altura_alvo6 = 150, 100

        imagem_redimensionada3 = ImageOps.fit(img_pil_correta3, (largura_alvo3, altura_alvo3), Image.Resampling.LANCZOS)
        imagem_redimensionada6 = ImageOps.fit(img_pil_correta6, (largura_alvo6, altura_alvo6), Image.Resampling.LANCZOS)
        imagem_redimensionada4 = ImageOps.fit(img_pil_correta4, (largura_alvo4, altura_alvo4), Image.Resampling.LANCZOS)
        imagem_redimensionada5 = ImageOps.fit(img_pil_correta5, (largura_alvo5, altura_alvo5), Image.Resampling.LANCZOS)

        imagem_tk3 = ImageTk.PhotoImage(imagem_redimensionada3)#image original
        imagem_tk6 = ImageTk.PhotoImage(imagem_redimensionada6)#image resultado
        imagem_tk4 = ImageTk.PhotoImage(imagem_redimensionada4)#image mascara
        imagem_tk5 = ImageTk.PhotoImage(imagem_redimensionada5)#image box 

        label_imagem3.config(image=imagem_tk3)
        label_imagem3.image = imagem_tk3
        
        label_imagem6.config(image=imagem_tk6)
        label_imagem6.image = imagem_tk6
        
        label_imagem4.config(image=imagem_tk4)
        label_imagem4.image = imagem_tk4

        label_imagem5.config(image=imagem_tk5)
        label_imagem5.image = imagem_tk5
        #------------------------------------------------------------
        global info
        info =classify_maturity(hsv, mask)          
        
#função de pagina menu
# Crie uma lista global (fora das funções) para rastrear os widgets da análise que precisam ser destruídos
widgets_analise = []


def mudar_para_analise():
    if not hasattr(label_imagem, "image") or label_imagem.image is None:
        messagebox.showerror(
            "Erro de Validação",
            "Por favor, Selecione e processe a imagem de um tomate antes de prosseguir para a análise profunda.",
        )
    else:
        global labels_dinamicas
        global verde
        global vermelho
        global laranja
        global widgets_analise

        labels_dinamicas = []

        for i, (key, value) in enumerate(info.items()):
            if isinstance(value, float):
                valor_formatado = f"{value:.2f}"
            else:
                valor_formatado = f"{value}"
            if i == 0:
                texto_exibido = f"{valor_formatado}"
                labels_dinamicas.append(texto_exibido)
            else:
                texto_exibido = f"{valor_formatado}%"
                labels_dinamicas.append(texto_exibido)

        cor_fundo_pagina = pagina_analise.cget("bg")

        esta = tk.Text(
            pagina_analise,
            font=("Arial", 12),
            bd=0,
            bg=cor_fundo_pagina,
            highlightthickness=0,
            height=2,
            width=50,       # 🚀 SOLUÇÃO: Garante espaço horizontal suficiente para não cortar
            wrap="word"  
        )
        esta.tag_configure("bold_tag", font=("Arial", 13, "bold"))
        esta.insert(tk.END, "Estágio de maturação identificado: ")
        esta.insert(tk.END, labels_dinamicas[0], "bold_tag")
        esta.config(state=tk.DISABLED)
        esta.grid(row=8, column=0, sticky="w", padx=5, pady=5)

        # SEPARAÇÃO DE LINHAS: Criamos primeiro, depois aplicamos o grid
        verde = tk.Label(
            pagina_analise,
            text=f"• Verde - {labels_dinamicas[1]}",
            anchor="center",
            justify="left",
            font=("Arial", 11),
            fg="green",
        )
        verde.grid(row=9, column=1, pady=20,padx=70, sticky="w")

        laranja = tk.Label(
            pagina_analise,
            text=f"• Laranja - {labels_dinamicas[2]}",
            anchor="center",
            justify="left",
            font=("Arial", 11),
            fg="#FF6600",
        )  # Seu laranja perfeito aqui!
        laranja.grid(row=10, column=1, pady=0, sticky="w",padx=70)

        vermelho = tk.Label(
            pagina_analise,
            text=f"• Vermelho - {labels_dinamicas[3]}",
            anchor="center",
            justify="left",
            font=("Arial", 11),
            fg="red",
        )
        vermelho.grid(row=11, column=1, pady=0, sticky="w",padx=70)

        caracteristica_cor = tk.Label(
            pagina_analise,
            text=f"• Valor médio da característica de cor analisada - {labels_dinamicas[4]}",
            font=("Arial", 11),
        )
        caracteristica_cor.grid(
            row=10, column=0, columnspan=4, pady=10, sticky="w"
        )

        # Guardamos todos esses componentes criados na lista para apagá-los depois
        widgets_analise = [esta, verde, laranja, vermelho, caracteristica_cor]

        pagina_menu.pack_forget()
        pagina_analise.pack()


# função da pagina analise
def voltar_para_menu():
    global widgets_analise

    # Destrói todos os textos antigos gerados na análise para não acumular na tela
    for widget in widgets_analise:
        widget.destroy()

    widgets_analise = []  # Limpa a lista de referências

    pagina_analise.pack_forget()
    pagina_menu.pack()

# --------------------- 
janela=tk.Tk()
janela.title('TomatoScan')
janela.geometry('1000x860+250+10')
pagina_menu=tk.Frame(janela)
pagina_menu.pack()
#-----------------------------------------------------------------------------------------------------------------------------
tk.Label(pagina_menu, text='Sistema de Visão Computacional para Identificação e Classificação Automática do Estágio de Maturação de Tomates. ',wraplength=750,justify='center', font=('Arial',17,'bold'), fg='darkblue').grid(row=0,columnspan=6,padx=20,pady=20)
texto1="O TomatoScan é um sistema que utiliza técnicas de processamento digital de imagens e análise de cores para identificar e classificar tomates em três estágios de maturação: verde, em maturação e maduro. "
tk.Label(pagina_menu, text=texto1, wraplength=700, justify="center", font=('Arial',11)).grid(row=1,columnspan=6,padx=20,pady=20)
tk.Button(pagina_menu, text="Selecionar imagem do tomate",wraplength=190, command=fazer_upload_nativo,font=('Arial',13,'bold'),fg="darkred").grid(row=2,column=1,padx=5,pady=50)
tk.Label(pagina_menu,text='Imagem selecionada para análise',font=('Arial',13,'bold')).grid(row=3,column=0,padx=20,pady=10)
tk.Label(pagina_menu,text='Imagem processada pelo sistema',font=('Arial',13,'bold')).grid(row=3,column=2,padx=20,pady=10)
tk.Label(pagina_menu,text='➡️',font=('Arial',27,'bold'),fg='blue',justify='center',anchor='center').grid(row=4,column=1,padx=5,pady=20)

container_imagem2 = tk.Frame(
    pagina_menu, width=350, height=250, bg="lightgray")
container_imagem2.grid_propagate(False)  # TRANCA O TAMANHO: Não deixa encolher nem crescer!
container_imagem2.grid(row=4,column=0,pady=20)
container_imagem2.rowconfigure(0, weight=1)
container_imagem2.columnconfigure(0, weight=1)
label_imagem2 = tk.Label(container_imagem2, bg='gray80')
label_imagem2.grid(row=0, column=0, sticky="nsew")

texto_aviso2 = tk.Label(container_imagem2, text="Nenhuma imagem selecionada", bg='gray80', wraplength=150, justify='center', anchor='center',font=('Arial',13,'bold'))
texto_aviso2.grid(row=0, column=0, sticky="") # Sem sticky para não esticar o fundo da letra, mantendo o centro puro

container_imagem = tk.Frame(
    pagina_menu, width=350, height=250, bg="lightgray")
container_imagem.grid_propagate(False)  # TRANCA O TAMANHO: Não deixa encolher nem crescer!
container_imagem.grid(row=4,column=2,pady=20)
container_imagem.rowconfigure(0, weight=1)
container_imagem.columnconfigure(0, weight=1)

label_imagem = tk.Label(container_imagem, bg='gray80')
label_imagem.grid(row=0, column=0, sticky="nsew")

texto_aviso = tk.Label(container_imagem, text="Nenhuma imagem selecionada", bg='gray80', wraplength=150, justify='center', anchor='center',font=('Arial',13,'bold'))
texto_aviso.grid(row=0, column=0, sticky="")

tk.Button(pagina_menu, text='Ver etapas da análise', command=mudar_para_analise,font=('Arial',12),fg="darkgreen").grid(row=5,column=1,padx=5,pady=20)
# -----------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------
# Rodapé Dividido: Texto Institucional na Esquerda e Créditos/Direitos na Direita
rodape_frame = tk.Frame(janela, bg="#e0e0e0", bd=1, relief=tk.SUNKEN)
rodape_frame.pack(side=tk.BOTTOM, fill=tk.X)

# Bloco 1: Lado Esquerdo (Instituição e Projeto)
texto_institucional = tk.Label(
    rodape_frame, 
    text="Instituto Federal de Educação, Ciência e Tecnologia de Rondônia (IFRO) — Campus Ariquemes\n"
         "Projeto de Ensino: Inteligência Artificial e Processamento Digital de Imagens com Python", 
    bg="#e0e0e0", 
    font=('Arial', 10), 
    justify='left',   
    anchor='w',       
    padx=15, 
    pady=10
)
texto_institucional.pack(side=tk.LEFT, fill=tk.X)

# Bloco 2: Lado Direito (Equipe, Orientadora e Copyright)
texto_creditos = tk.Label(
    rodape_frame, 
    text="Equipe de desenvolvimento: Carlos Santos, Thaison Goes\n"
         "Orientadora: Camila Silva dos Santos\n"
         "© 2026 TomatoScan v1.0. Todos os direitos reservados.", 
    bg="#e0e0e0", 
    font=('Arial', 10), 
    justify='right',  # Alinha as linhas internas à direita
    anchor='e',       # Alinha a caixa à direita (East)
    padx=15, 
    pady=10
)
texto_creditos.pack(side=tk.RIGHT, fill=tk.X, expand=True)

#-----------------------------------------------------------------------------------
#pagina analise
pagina_analise=tk.Frame()

tk.Label(pagina_analise,text='Distribuição das cores do fruto',justify='left',anchor='center',font=('arial',13,'bold')).grid(row=8,column=1)
tk.Label(pagina_analise,text='Matiz médio (Hue)',justify='left',anchor='w',font=('Aril',13,'bold')).grid(row=9,column=0,sticky="w")
tk.Label(pagina_analise,text='RESULTADO DA ANÁLISE ',
         font=('Aril',15,"bold"),
         fg='darkgreen').grid(row=7,columnspan=6,padx=10,pady=10)
tk.Button(pagina_analise,text='Voltar',
          command=voltar_para_menu,
          font=('Arial',12,'bold'),
          fg='blue').grid(row=11,columnspan=6,padx=10,pady=10)
tk.Label(pagina_analise,
         text='Processos da Análise',
         font=('Arial',20,'bold'),
         fg='darkblue').grid(row=0,columnspan=6,padx=10,pady=10)
tk.Label(pagina_analise,text='Etapa 1 — Imagem original',
         anchor='center',
         font=('Aril',13,'bold')).grid(row=1,column=0,padx=10,pady=10)
tk.Label(pagina_analise,text='Etapa 2 — Segmentação do tomate',
         anchor='center',
         font=('Aril',13,'bold')).grid(row=1,column=1,padx=10,pady=10)
tk.Label(pagina_analise,text='Etapa 3 — Localização do fruto',
         anchor='center',
         font=('Aril',13,'bold')).grid(row=4,column=0,padx=10,pady=10)
tk.Label(pagina_analise,text='Etapa 4 — Resultado da análise ',
         anchor='center',
         font=('Aril',13,'bold')).grid(row=4,column=1,padx=10,pady=10)

tk.Label(pagina_analise,text='Apresenta a fotografia utilizada como entrada do sistema, que será submetida às etapas de processamento. ',wraplength=270,justify='left',anchor='w').grid(row=2,column=0)
tk.Label(pagina_analise,text='Gera uma máscara para separar a região identificada como tomate do restante da imagem, permitindo analisar o fruto isoladamente.',wraplength=270,justify='left',anchor='w').grid(row=2,column=1)
tk.Label(pagina_analise,text='Delimita a região do tomate por meio de uma caixa delimitadora (bounding box), facilitando a visualização de sua localização.',wraplength=270,justify='left',anchor='w').grid(row=5,column=0)
tk.Label(pagina_analise,text='Apresenta o fruto localizado e a classificação estimada pelo algoritmo, conforme as características analisadas na imagem.',wraplength=270,justify='left',anchor='w').grid(row=5,column=1)

container_imagem3 = tk.Frame(
    pagina_analise, width=150, height=100, bg="lightgray")
container_imagem3.grid_propagate(False)  # TRANCA O TAMANHO: Não deixa encolher nem crescer!
container_imagem3.grid(row=3,column=0,pady=20)
container_imagem3.rowconfigure(0, weight=1)
container_imagem3.columnconfigure(0, weight=1)

label_imagem3 = tk.Label(container_imagem3, bg='gray80')
label_imagem3.grid(row=0, column=0, sticky="nsew")

container_imagem4 = tk.Frame(
    pagina_analise, width=150, height=100, bg="lightgray")
container_imagem4.grid_propagate(False)  # TRANCA O TAMANHO: Não deixa encolher nem crescer!
container_imagem4.grid(row=3,column=1,pady=20)
container_imagem4.rowconfigure(0, weight=1)
container_imagem4.columnconfigure(0, weight=1)

label_imagem4 = tk.Label(container_imagem4, bg='gray80')
label_imagem4.grid(row=0, column=0, sticky="nsew")

container_imagem5 = tk.Frame(
    pagina_analise, width=150, height=100, bg="lightgray")
container_imagem5.grid_propagate(False)  # TRANCA O TAMANHO: Não deixa encolher nem crescer!
container_imagem5.grid(row=6,column=0,pady=20)
container_imagem5.rowconfigure(0, weight=1)
container_imagem5.columnconfigure(0, weight=1)

label_imagem5 = tk.Label(container_imagem5, bg='gray80')
label_imagem5.grid(row=0, column=0, sticky="nsew")

container_imagem6 = tk.Frame(
    pagina_analise, width=150, height=100, bg="lightgray")
container_imagem6.grid_propagate(False)  # TRANCA O TAMANHO: Não deixa encolher nem crescer!
container_imagem6.grid(row=6,column=1,pady=20)
container_imagem6.rowconfigure(0, weight=1)
container_imagem6.columnconfigure(0, weight=1)
label_imagem6 = tk.Label(container_imagem6, bg='gray80')
label_imagem6.grid(row=0, column=0, sticky="nsew")

janela.mainloop()