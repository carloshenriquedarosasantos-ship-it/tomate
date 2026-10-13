import tkinter as tk
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from tkinter import filedialog 
from PIL import Image, ImageTk,ImageOps
from tkinter import messagebox   
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
        "estagio": stage,
        "verde_pct": green_pct,
        "laranja_pct": orange_pct,
        "vermelho_pct": red_pct,
        "hue_medio": hue_mean
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
        f"{info['estagio']} | "
        f"V:{info['verde_pct']:.1f}% "
        f"L:{info['laranja_pct']:.1f}% "
        f"R:{info['vermelho_pct']:.1f}%"
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

        img_pil_correta = Image.fromarray(imgem_resulta_rgb)
        
        # Pega automaticamente a largura e altura exata que você travou no seu quadrado cinza
        largura_alvo = container_imagem.winfo_width()
        altura_alvo = container_imagem.winfo_height()
        
        # Garante um tamanho mínimo caso a função seja chamada antes da janela renderizar totalmente
        if largura_alvo <= 1: 
            largura_alvo, altura_alvo = 300, 200 

        # Ajusta a foto para preencher 100% do espaço disponível no quadrado cinza
        imagem_redimensionada = ImageOps.fit(img_pil_correta, (largura_alvo, altura_alvo), Image.Resampling.LANCZOS)

        imagem_tk = ImageTk.PhotoImage(imagem_redimensionada)

        # Atualiza a interface mantendo o preenchimento total
        label_imagem.config(image=imagem_tk, text="")
        label_imagem.image = imagem_tk

#função de pagina menu
def mudar_para_analise():
    # Verifica se o rótulo ainda exibe o texto padrão (ou seja, nenhuma imagem foi carregada)
    if label_imagem.cget("text") == "Nenhuma imagem selecionada":
        messagebox.showerror(
            "Erro de Validação", 
            "Por favor, Selecione e processe a imagem de um tomate antes de prosseguir para a análise profunda."
        )
    else:
        # Se houver uma imagem, o botão funciona normalmente e troca de página
        pagina_menu.pack_forget()
        pagina_analise.pack()

#função da pagina analise
def voltar_para_menu():
    pagina_analise.pack_forget()
    pagina_menu.pack()
#------------------------------------------------------ 
janela=tk.Tk()
janela.title('TomatoScan')
janela.geometry('900x800+250+25')

# Página Menu expandindo por completo
pagina_menu=tk.Frame(janela)
pagina_menu.pack()

#-----------------------------------------------------------------------------------------------------------------------------
tk.Label(pagina_menu, text='Identificador de Maturação de Tomate', font=('Arial',20,'bold'), fg='darkblue').grid(row=0,columnspan=6,padx=20,pady=20)
texto1="É um sistema de visão computacional para identificar e classificar tomates de acordo com seu estágio de maturação em três categorias: verde, em maturação e maduro."
tk.Label(pagina_menu, text=texto1, wraplength=700, justify="left", font=('Arial',12)).grid(row=1,columnspan=6,padx=20,pady=20)
tk.Button(pagina_menu, text="Escolher uma imagem de um tomate", command=fazer_upload_nativo,wraplength=160,font=('Arial',15,'bold'),fg="darkred").grid(row=2,column=0,padx=5,pady=50)

container_imagem = tk.Frame(
    pagina_menu, width=300, height=200, bg="lightgray")
container_imagem.grid_propagate(False)  # TRANCA O TAMANHO: Não deixa encolher nem crescer!
container_imagem.grid(row=2,column=2,pady=20)
container_imagem.rowconfigure(0, weight=1)
container_imagem.columnconfigure(0, weight=1)
label_imagem = tk.Label(
    container_imagem, 
    text="Nenhuma imagem selecionada",
    justify="center", 
    anchor="center",     
    bg="lightgray", 
    fg="black", 
    wraplength=150, 
    font=('Sans', 20)
)

label_imagem.grid(row=0, column=0, sticky="nsew")

tk.Button(pagina_menu, text='Análise profunda', command=mudar_para_analise,font=('Arial',12),fg="blue").grid(row=3,column=1,padx=40,pady=40)

# -----------------------------------------------------------------------------------
rodape_frame = tk.Frame(janela, bg="#e0e0e0", bd=1, relief=tk.SUNKEN)
rodape_frame.pack(side=tk.BOTTOM, fill=tk.X)

# 1. TEXTO DO RODAPÉ (Alinhado à ESQUERDA)
texto_rodape = tk.Label(
    rodape_frame, 
    text="TomatoScan v1.0 — Todos os direitos reservados ao projeto de ensino IFRO Vision Lab .", 
    bg="#e0e0e0", 
    font=('Arial', 10),
    padx=15,
    pady=8
)
texto_rodape.pack(side=tk.LEFT)  # <--- Cola na esquerda

# 2. LOGO DO RODAPÉ (Alinhada à DIREITA com verificação de segurança)
caminho_png = "logo-ifro-hotsite.png"

try:
    img_rodape_png = tk.PhotoImage(file=caminho_png)
    img_rodape_png = img_rodape_png.subsample(10, 10) 

     

    logo_rodape = tk.Label(
        rodape_frame, 
        image=img_rodape_png, 
        bg="#e0e0e0",
        padx=15
    )
    logo_rodape.image = img_rodape_png  
    logo_rodape.pack(side=tk.RIGHT)     # <--- Cola na direita

except tk.TclError:
    
    logo_rodape = tk.Label(
        rodape_frame, 
        text="[Logo Ausente]", 
        fg="gray",
        bg="#e0e0e0",
        padx=15
    )
    logo_rodape.pack(side=tk.RIGHT)


#-----------------------------------------------------------------------------------
#pagina analise
pagina_analise=tk.Frame()
tk.Button(pagina_analise,text='Voltar',command=voltar_para_menu,).pack()



janela.mainloop()