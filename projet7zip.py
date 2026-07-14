"""
Projet7Zip — Logiciel de compression/décompression
Interface graphique Tkinter
Méthodes : RLE, LZ77, LZW, Arithmétique
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from algorithms import compress_file, decompress_file, METHODS


# ══════════════════════════════════════════════════════════════
#  PALETTE DE COULEURS
# ══════════════════════════════════════════════════════════════
BG        = "#1a1a2e"
BG2       = "#16213e"
BG3       = "#0f3460"
ACCENT    = "#e94560"
ACCENT2   = "#4ecca3"
TEXT      = "#eaeaea"
TEXT2     = "#aaaaaa"
CARD      = "#1e2a45"
SUCCESS   = "#4ecca3"
WARNING   = "#f5a623"
DANGER    = "#e94560"
BORDER    = "#2a3f6f"


# ══════════════════════════════════════════════════════════════
#  COMPOSANTS UI RÉUTILISABLES
# ══════════════════════════════════════════════════════════════

def make_card(parent, **kwargs):
    f = tk.Frame(parent, bg=CARD, bd=0, highlightbackground=BORDER,
                 highlightthickness=1, **kwargs)
    return f

def label(parent, text, size=11, color=TEXT, bold=False, **kw):
    font = ("Segoe UI", size, "bold" if bold else "normal")
    return tk.Label(parent, text=text, font=font, bg=kw.pop("bg", parent["bg"]),
                    fg=color, **kw)

def btn(parent, text, cmd, color=ACCENT, fg=TEXT, width=18, **kw):
    b = tk.Button(parent, text=text, command=cmd,
                  bg=color, fg=fg, activebackground=ACCENT2,
                  activeforeground=BG, font=("Segoe UI", 10, "bold"),
                  relief="flat", cursor="hand2", width=width,
                  padx=10, pady=6, bd=0, **kw)
    b.bind("<Enter>", lambda e: b.config(bg=ACCENT2, fg=BG))
    b.bind("<Leave>", lambda e: b.config(bg=color, fg=fg))
    return b


# ══════════════════════════════════════════════════════════════
#  FENÊTRE PRINCIPALE
# ══════════════════════════════════════════════════════════════

class Projet7Zip(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Projet7Zip")
        self.geometry("900x680")
        self.minsize(800, 600)
        self.configure(bg=BG)
        self.resizable(True, True)

        # État
        self.selected_files   = []
        self.output_dir       = tk.StringVar(value=os.path.expanduser("~"))
        self.method           = tk.StringVar(value="LZW")
        self.mode             = tk.StringVar(value="compress")
        self.history          = []   # [(action, fichier, ratio, taille, durée)]

        self._build_ui()
        self._update_mode()

    # ────────────────────────────────────────────────────────
    #  Construction UI
    # ────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Barre de titre ──
        self._build_titlebar()
        # ── Contenu principal (sidebar + zone centrale) ──
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=0, pady=0)
        self._build_sidebar(main)
        self._build_center(main)
        # ── Barre de statut ──
        self._build_statusbar()

    def _build_titlebar(self):
        bar = tk.Frame(self, bg=BG3, height=56)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Logo
        tk.Label(bar, text="  🗜 ", font=("Segoe UI", 22), bg=BG3, fg=ACCENT).pack(side="left")
        tk.Label(bar, text="Projet7Zip", font=("Segoe UI", 16, "bold"),
                 bg=BG3, fg=TEXT).pack(side="left", pady=12)
        tk.Label(bar, text=" v1.0", font=("Segoe UI", 10),
                 bg=BG3, fg=TEXT2).pack(side="left", pady=14)

        # Badges méthodes à droite
        for m in ["RLE", "LZ77", "LZW", "Arithmétique"]:
            tk.Label(bar, text=f" {m} ", font=("Segoe UI", 9, "bold"),
                     bg=ACCENT, fg="white", padx=4, pady=2).pack(
                side="right", padx=4, pady=14)

    def _build_sidebar(self, parent):
        side = tk.Frame(parent, bg=BG2, width=220)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        label(side, "  NAVIGATION", 9, TEXT2, bg=BG2).pack(anchor="w", pady=(18, 4))

        nav_items = [
            ("🗜  Compression",   "compress"),
            ("📂  Décompression", "decompress"),
            ("📊  Historique",    "history"),
            ("ℹ️   À propos",      "about"),
        ]
        self._nav_btns = {}
        for text, key in nav_items:
            b = tk.Button(side, text=text,
                          font=("Segoe UI", 11), bg=BG2, fg=TEXT,
                          activebackground=BG3, activeforeground=ACCENT,
                          relief="flat", anchor="w", padx=18, pady=10,
                          cursor="hand2", bd=0,
                          command=lambda k=key: self._switch_page(k))
            b.pack(fill="x")
            self._nav_btns[key] = b

        # Séparateur
        tk.Frame(side, bg=BORDER, height=1).pack(fill="x", padx=14, pady=12)

        # Méthode rapide
        label(side, "  MÉTHODE", 9, TEXT2, bg=BG2).pack(anchor="w", pady=(0,4))
        for m in ["RLE", "LZ77", "LZW", "Arithmétique"]:
            rb = tk.Radiobutton(side, text=f"  {m}",
                                variable=self.method, value=m,
                                font=("Segoe UI", 10), bg=BG2, fg=TEXT,
                                selectcolor=BG3, activebackground=BG2,
                                activeforeground=ACCENT2,
                                relief="flat", cursor="hand2")
            rb.pack(anchor="w", padx=10, pady=2)

        # Info méthode
        tk.Frame(side, bg=BORDER, height=1).pack(fill="x", padx=14, pady=12)
        self._method_info = label(side, "", 8, TEXT2, bg=BG2, wraplength=190, justify="left")
        self._method_info.pack(anchor="w", padx=14)
        self.method.trace("w", lambda *_: self._update_method_info())
        self._update_method_info()

    def _build_center(self, parent):
        self._center = tk.Frame(parent, bg=BG)
        self._center.pack(side="left", fill="both", expand=True)

        # Pages
        self._pages = {}
        self._pages["compress"]   = self._page_compress()
        self._pages["decompress"] = self._page_decompress()
        self._pages["history"]    = self._page_history()
        self._pages["about"]      = self._page_about()

        self._switch_page("compress")

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=BG3, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self._status_var = tk.StringVar(value="Prêt.")
        tk.Label(bar, textvariable=self._status_var,
                 font=("Segoe UI", 9), bg=BG3, fg=TEXT2).pack(side="left", padx=12)
        tk.Label(bar, text="Projet7Zip © 2025 — RLE | LZ77 | LZW | Arithmétique",
                 font=("Segoe UI", 9), bg=BG3, fg=TEXT2).pack(side="right", padx=12)

    # ────────────────────────────────────────────────────────
    #  PAGE — COMPRESSION
    # ────────────────────────────────────────────────────────

    def _page_compress(self):
        page = tk.Frame(self._center, bg=BG)

        # Titre
        hdr = tk.Frame(page, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        label(hdr, "Compression de fichiers", 16, TEXT, bold=True, bg=BG).pack(side="left")

        # Zone sélection fichiers
        card1 = make_card(page)
        card1.pack(fill="x", padx=24, pady=6)
        r = tk.Frame(card1, bg=CARD)
        r.pack(fill="x", padx=16, pady=12)
        label(r, "📁  Fichiers à compresser", 11, TEXT2, bold=True, bg=CARD).pack(side="left")
        #btn(r, "+ Ajouter fichiers", self._add_files, width=16).pack(side="right", padx=4)
        btn(
            r,
            "+ Fichiers",
            self._add_files,
            width=12
        ).pack(side="right", padx=4)

        btn(
            r,
            "📁 Dossier",
            self._add_folder,
            width=12
        ).pack(side="right", padx=4)
        btn(r, "Vider", self._clear_files, color=BG3, width=8).pack(side="right", padx=4)

        # Liste des fichiers
        list_frame = tk.Frame(card1, bg=BG2, bd=0)
        list_frame.pack(fill="x", padx=16, pady=(0, 12))
        self._file_listbox = tk.Listbox(list_frame, bg=BG2, fg=TEXT,
                                        selectbackground=BG3,
                                        selectforeground=ACCENT,
                                        font=("Segoe UI", 10),
                                        height=5, bd=0, relief="flat",
                                        highlightthickness=0)
        self._file_listbox.pack(fill="x", side="left", expand=True)
        sb = ttk.Scrollbar(list_frame, command=self._file_listbox.yview)
        sb.pack(side="right", fill="y")
        self._file_listbox.config(yscrollcommand=sb.set)

        # Dossier de sortie
        card2 = make_card(page)
        card2.pack(fill="x", padx=24, pady=6)
        r2 = tk.Frame(card2, bg=CARD)
        r2.pack(fill="x", padx=16, pady=12)
        label(r2, "📂  Dossier de sortie", 11, TEXT2, bold=True, bg=CARD).pack(anchor="w")
        row = tk.Frame(card2, bg=CARD)
        row.pack(fill="x", padx=16, pady=(0,12))
        tk.Entry(row, textvariable=self.output_dir, bg=BG2, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=("Segoe UI", 10),
                 highlightbackground=BORDER, highlightthickness=1).pack(
            side="left", fill="x", expand=True, ipady=5)
        btn(row, "Choisir", self._choose_outdir, width=10, color=BG3).pack(side="right", padx=(8,0))

        # Options méthode
        card3 = make_card(page)
        card3.pack(fill="x", padx=24, pady=6)
        r3 = tk.Frame(card3, bg=CARD)
        r3.pack(fill="x", padx=16, pady=10)
        label(r3, "⚙️  Méthode de compression", 11, TEXT2, bold=True, bg=CARD).pack(anchor="w")
        rb_row = tk.Frame(card3, bg=CARD)
        rb_row.pack(fill="x", padx=16, pady=(0,10))
        method_desc = {
            "RLE":          "Rapide, idéal pour données répétitives",
            "LZ77":         "Fenêtre glissante, bon équilibre",
            "LZW":          "Dictionnaire dynamique, fichiers texte",
            "Arithmétique": "Probabilités, haute compression",
        }
        for m, desc in method_desc.items():
            col = tk.Frame(rb_row, bg=CARD)
            col.pack(side="left", padx=10)
            rb = tk.Radiobutton(col, text=m, variable=self.method, value=m,
                                font=("Segoe UI", 10, "bold"), bg=CARD, fg=TEXT,
                                selectcolor=BG3, activebackground=CARD,
                                activeforeground=ACCENT2, relief="flat", cursor="hand2")
            rb.pack(anchor="w")
            label(col, desc, 8, TEXT2, bg=CARD).pack(anchor="w")

        # Barre de progression
        prog_frame = tk.Frame(page, bg=BG)
        prog_frame.pack(fill="x", padx=24, pady=6)
        self._prog_label_c = label(prog_frame, "", 9, TEXT2, bg=BG)
        self._prog_label_c.pack(anchor="w")
        self._progress_c = ttk.Progressbar(prog_frame, length=400,
                                           mode="determinate", maximum=100)
        self._progress_c.pack(fill="x", pady=4)

        # Bouton compresser
        btn_row = tk.Frame(page, bg=BG)
        btn_row.pack(pady=14)
        btn(btn_row, "🗜  COMPRESSER", self._run_compress,
            color=ACCENT, width=22).pack(side="left", padx=8)

        # Résultat
        self._result_c = make_card(page)
        self._result_c.pack(fill="x", padx=24, pady=6)
        self._result_c_inner = tk.Frame(self._result_c, bg=CARD)
        self._result_c_inner.pack(fill="x", padx=16, pady=12)

        return page

    # ────────────────────────────────────────────────────────
    #  PAGE — DÉCOMPRESSION
    # ────────────────────────────────────────────────────────

    def _page_decompress(self):
        page = tk.Frame(self._center, bg=BG)

        hdr = tk.Frame(page, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        label(hdr, "Décompression de fichiers", 16, TEXT, bold=True, bg=BG).pack(side="left")

        # Fichier source
        card1 = make_card(page)
        card1.pack(fill="x", padx=24, pady=6)
        r = tk.Frame(card1, bg=CARD)
        r.pack(fill="x", padx=16, pady=12)
        label(r, "📦  Fichier .p7z à décompresser", 11, TEXT2, bold=True, bg=CARD).pack(anchor="w")
        row = tk.Frame(card1, bg=CARD)
        row.pack(fill="x", padx=16, pady=(0,12))
        self._decomp_src = tk.StringVar()
        tk.Entry(row, textvariable=self._decomp_src, bg=BG2, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=("Segoe UI", 10),
                 highlightbackground=BORDER, highlightthickness=1).pack(
            side="left", fill="x", expand=True, ipady=5)
        btn(row, "Parcourir", self._browse_p7z, width=12, color=BG3).pack(side="right", padx=(8,0))

        # Dossier de sortie
        card2 = make_card(page)
        card2.pack(fill="x", padx=24, pady=6)
        r2 = tk.Frame(card2, bg=CARD)
        r2.pack(fill="x", padx=16, pady=12)
        label(r2, "📂  Dossier de sortie", 11, TEXT2, bold=True, bg=CARD).pack(anchor="w")
        row2 = tk.Frame(card2, bg=CARD)
        row2.pack(fill="x", padx=16, pady=(0,12))
        self._decomp_dst = tk.StringVar(value=os.path.expanduser("~"))
        tk.Entry(row2, textvariable=self._decomp_dst, bg=BG2, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=("Segoe UI", 10),
                 highlightbackground=BORDER, highlightthickness=1).pack(
            side="left", fill="x", expand=True, ipady=5)
        btn(row2, "Choisir", self._choose_decomp_dir, width=10, color=BG3).pack(side="right", padx=(8,0))

        # Progression
        prog_frame = tk.Frame(page, bg=BG)
        prog_frame.pack(fill="x", padx=24, pady=6)
        self._prog_label_d = label(prog_frame, "", 9, TEXT2, bg=BG)
        self._prog_label_d.pack(anchor="w")
        self._progress_d = ttk.Progressbar(prog_frame, length=400,
                                           mode="determinate", maximum=100)
        self._progress_d.pack(fill="x", pady=4)

        # Bouton
        btn_row = tk.Frame(page, bg=BG)
        btn_row.pack(pady=14)
        btn(btn_row, "📂  DÉCOMPRESSER", self._run_decompress,
            color=ACCENT2, fg=BG, width=22).pack(side="left", padx=8)

        # Résultat
        self._result_d = make_card(page)
        self._result_d.pack(fill="x", padx=24, pady=6)
        self._result_d_inner = tk.Frame(self._result_d, bg=CARD)
        self._result_d_inner.pack(fill="x", padx=16, pady=12)

        return page

    # ────────────────────────────────────────────────────────
    #  PAGE — HISTORIQUE
    # ────────────────────────────────────────────────────────

    def _page_history(self):
        page = tk.Frame(self._center, bg=BG)

        hdr = tk.Frame(page, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(20, 8))
        label(hdr, "Historique des opérations", 16, TEXT, bold=True, bg=BG).pack(side="left")
        btn(hdr, "🗑 Vider", self._clear_history, color=DANGER, width=10).pack(side="right")

        # Tableau
        card = make_card(page)
        card.pack(fill="both", expand=True, padx=24, pady=6)

        cols = ("Action", "Fichier", "Méthode", "Taille orig.", "Taille sortie", "Ratio", "Durée")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview",
                        background=BG2, foreground=TEXT,
                        fieldbackground=BG2, rowheight=28,
                        font=("Segoe UI", 10))
        style.configure("Custom.Treeview.Heading",
                        background=BG3, foreground=TEXT,
                        font=("Segoe UI", 10, "bold"))
        style.map("Custom.Treeview",
                  background=[("selected", BG3)],
                  foreground=[("selected", ACCENT)])

        self._hist_tree = ttk.Treeview(card, columns=cols, show="headings",
                                       style="Custom.Treeview")
        widths = [110, 180, 110, 100, 100, 80, 70]
        for col, w in zip(cols, widths):
            self._hist_tree.heading(col, text=col)
            self._hist_tree.column(col, width=w, anchor="center")
        self._hist_tree.pack(fill="both", expand=True, padx=8, pady=8)

        vsb = ttk.Scrollbar(card, orient="vertical", command=self._hist_tree.yview)
        self._hist_tree.configure(yscrollcommand=vsb.set)

        return page

    # ────────────────────────────────────────────────────────
    #  PAGE — À PROPOS
    # ────────────────────────────────────────────────────────

    def _page_about(self):
        page = tk.Frame(self._center, bg=BG)

        tk.Frame(page, bg=BG, height=30).pack()
        label(page, "🗜  Projet7Zip", 28, ACCENT, bold=True, bg=BG).pack()
        label(page, "Logiciel de compression / décompression", 13, TEXT2, bg=BG).pack(pady=4)
        label(page, "v1.0 — 2025", 10, TEXT2, bg=BG).pack()

        tk.Frame(page, bg=BORDER, height=1).pack(fill="x", padx=60, pady=20)

        methods_info = [
            ("RLE", "Run-Length Encoding",
             "Compresse les séquences répétitives.\nIdéal pour images simples et données binaires répétitives."),
            ("LZ77", "Lempel-Ziv 1977",
             "Fenêtre glissante avec triplets (dist, long, car).\nBon équilibre vitesse / compression."),
            ("LZW", "Lempel-Ziv-Welch",
             "Dictionnaire dynamique auto-construit.\nTrès efficace pour textes et fichiers mixtes."),
            ("Arithmétique", "Codage Arithmétique",
             "Encode par probabilités cumulées.\nHaute compression, idéal pour textes naturels."),
        ]

        cards_frame = tk.Frame(page, bg=BG)
        cards_frame.pack(padx=30, fill="x")
        for i, (short, full, desc) in enumerate(methods_info):
            c = make_card(cards_frame)
            c.grid(row=i//2, column=i%2, padx=10, pady=8, sticky="nsew")
            cards_frame.columnconfigure(i%2, weight=1)
            label(c, short, 14, ACCENT, bold=True, bg=CARD).pack(anchor="w", padx=14, pady=(12,2))
            label(c, full, 10, ACCENT2, bg=CARD).pack(anchor="w", padx=14)
            label(c, desc, 9, TEXT2, bg=CARD, justify="left", wraplength=280).pack(
                anchor="w", padx=14, pady=(4,12))

        tk.Frame(page, bg=BORDER, height=1).pack(fill="x", padx=60, pady=16)
        label(page, "Format de fichier : .p7z", 10, TEXT2, bg=BG).pack()
        label(page, "Extension propriétaire — entête Magic + ID méthode + données compressées", 9, TEXT2, bg=BG).pack()

        return page

    # ────────────────────────────────────────────────────────
    #  NAVIGATION
    # ────────────────────────────────────────────────────────

    def _switch_page(self, key):
        for k, p in self._pages.items():
            p.pack_forget()
        self._pages[key].pack(fill="both", expand=True)
        # Mettre à jour sidebar
        for k, b in self._nav_btns.items():
            b.config(bg=BG3 if k == key else BG2,
                     fg=ACCENT if k == key else TEXT)
        self.mode.set(key)

    def _update_mode(self):
        pass

    # ────────────────────────────────────────────────────────
    #  ACTIONS — FICHIERS
    # ────────────────────────────────────────────────────────

    def _add_files(self):
        files = filedialog.askopenfilenames(
            title="Sélectionner des fichiers à compresser",
            filetypes=[("Tous les fichiers", "*.*")])
        for f in files:
            if f not in self.selected_files:
                self.selected_files.append(f)
                self._file_listbox.insert("end", f"  {os.path.basename(f)}")
        self._status("  " + str(len(self.selected_files)) + " fichier(s) sélectionné(s).")

    def _clear_files(self):
        self.selected_files.clear()
        self._file_listbox.delete(0, "end")

    def _choose_outdir(self):
        d = filedialog.askdirectory(title="Choisir le dossier de sortie")
        if d:
            self.output_dir.set(d)

    def _choose_decomp_dir(self):
        d = filedialog.askdirectory(title="Choisir le dossier de sortie")
        if d:
            self._decomp_dst.set(d)

    def _browse_p7z(self):
        f = filedialog.askopenfilename(
            title="Ouvrir un fichier .p7z",
            filetypes=[("Fichiers P7Z", "*.p7z"), ("Tous", "*.*")])
        if f:
            self._decomp_src.set(f)

    def _add_folder(self):

        folder = filedialog.askdirectory(
            title="Sélectionner un dossier à compresser"
        )

        if folder:

            if folder not in self.selected_files:
                self.selected_files.append(folder)

                self._file_listbox.insert(
                    "end",
                    "📁 " + os.path.basename(folder)
                )

            self._status(
                "Dossier ajouté."
            )

    # ────────────────────────────────────────────────────────
    #  ACTIONS — COMPRESSION
    # ────────────────────────────────────────────────────────

    def _run_compress(self):
        if not self.selected_files:
            messagebox.showwarning("Attention", "Aucun fichier sélectionné.")
            return
        out = self.output_dir.get()
        if not os.path.isdir(out):
            messagebox.showerror("Erreur", "Dossier de sortie invalide.")
            return
        method = self.method.get()
        threading.Thread(target=self._compress_thread,
                         args=(list(self.selected_files), out, method),
                         daemon=True).start()

    def _compress_thread(self, files, out_dir, method):
        results = []
        for i, src in enumerate(files):
            self._set_progress_c(0, f"Compression de {os.path.basename(src)}…")
            dst = os.path.join(out_dir, os.path.basename(src) + ".p7z")
            try:
                stats = compress_file(src, dst,
                                      method=method,
                                      progress_cb=self._set_progress_c)
                results.append((src, dst, stats))
                self._add_history("Compression", os.path.basename(src),
                                  stats["method"], stats["orig_size"],
                                  stats["comp_size"], stats["ratio"],
                                  stats["elapsed"])
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror("Erreur", err))
                return

        self.after(0, lambda: self._show_compress_results(results))

    def _show_compress_results(self, results):
        for w in self._result_c_inner.winfo_children():
            w.destroy()
        label(self._result_c_inner, "✅  Résultats", 11, SUCCESS, bold=True, bg=CARD).pack(anchor="w")
        for src, dst, s in results:
            row = tk.Frame(self._result_c_inner, bg=CARD)
            row.pack(fill="x", pady=3)
            label(row, f"📄 {os.path.basename(src)}", 10, TEXT, bg=CARD).pack(side="left")
            label(row, f"{self._fmt(s['orig_size'])} → {self._fmt(s['comp_size'])}",
                  10, TEXT2, bg=CARD).pack(side="left", padx=20)
            ratio_col = SUCCESS if s["ratio"] > 0 else WARNING
            label(row, f"{'%.1f' % s['ratio']}% {'gagné' if s['ratio']>0 else 'expansion'}",
                  10, ratio_col, bg=CARD).pack(side="left")
            label(row, f"⏱ {'%.2f' % s['elapsed']}s", 10, TEXT2, bg=CARD).pack(side="right")

    # ────────────────────────────────────────────────────────
    #  ACTIONS — DÉCOMPRESSION
    # ────────────────────────────────────────────────────────

    def _run_decompress(self):
        src = self._decomp_src.get()
        if not src or not os.path.isfile(src):
            messagebox.showwarning("Attention", "Veuillez sélectionner un fichier .p7z valide.")
            return
        dst = self._decomp_dst.get()
        if not os.path.isdir(dst):
            messagebox.showerror("Erreur", "Dossier de sortie invalide.")
            return
        threading.Thread(target=self._decompress_thread,
                         args=(src, dst), daemon=True).start()

    def _decompress_thread(self, src, dst_dir):
        self._set_progress_d(0, "Décompression en cours…")
        try:
            stats = decompress_file(src, dst_dir,
                                    progress_cb=self._set_progress_d)
            self._add_history("Décompression", stats["orig_name"],
                              stats["method"], stats["comp_size"],
                              stats["orig_size"], stats["ratio"],
                              stats["elapsed"])
            self.after(0, lambda: self._show_decompress_result(stats))
        except Exception as e:
            self.after(0, lambda err=str(e): messagebox.showerror("Erreur", err))

    def _show_decompress_result(self, s):
        for w in self._result_d_inner.winfo_children():
            w.destroy()
        label(self._result_d_inner, "✅  Décompression réussie", 11, SUCCESS, bold=True, bg=CARD).pack(anchor="w")
        row1 = tk.Frame(self._result_d_inner, bg=CARD)
        row1.pack(fill="x", pady=4)
        label(row1, f"📄 Fichier : {s['orig_name']}", 10, TEXT, bg=CARD).pack(side="left")
        label(row1, f"Méthode : {s['method']}", 10, ACCENT2, bg=CARD).pack(side="left", padx=20)
        row2 = tk.Frame(self._result_d_inner, bg=CARD)
        row2.pack(fill="x")
        label(row2, f"📂 Enregistré dans : {s['out_path']}", 9, TEXT2, bg=CARD).pack(side="left")
        label(row2, f"⏱ {'%.2f' % s['elapsed']}s", 10, TEXT2, bg=CARD).pack(side="right")

    # ────────────────────────────────────────────────────────
    #  HISTORIQUE
    # ────────────────────────────────────────────────────────

    def _add_history(self, action, name, method, orig, comp, ratio, elapsed):
        row = (action, name, method,
               self._fmt(orig), self._fmt(comp),
               f"{'%.1f' % ratio}%",
               f"{'%.2f' % elapsed}s")
        self.history.append(row)
        self.after(0, lambda r=row: self._hist_tree.insert("", 0, values=r))

    def _clear_history(self):
        self.history.clear()
        for item in self._hist_tree.get_children():
            self._hist_tree.delete(item)

    # ────────────────────────────────────────────────────────
    #  PROGRESSION
    # ────────────────────────────────────────────────────────

    def _set_progress_c(self, val, msg=""):
        self.after(0, lambda: [
            self._progress_c.config(value=val),
            self._prog_label_c.config(text=msg),
            self._status(msg),
        ])

    def _set_progress_d(self, val, msg=""):
        self.after(0, lambda: [
            self._progress_d.config(value=val),
            self._prog_label_d.config(text=msg),
            self._status(msg),
        ])

    def _status(self, msg):
        self._status_var.set(f"  {msg}")

    # ────────────────────────────────────────────────────────
    #  MÉTHODE INFO (sidebar)
    # ────────────────────────────────────────────────────────

    def _update_method_info(self):
        infos = {
            "RLE":          "✦ Rapide\n✦ Données répétitives\n✦ Compression modérée",
            "LZ77":         "✦ Fenêtre glissante\n✦ Bon équilibre\n✦ Fichiers variés",
            "LZW":          "✦ Dictionnaire dynamique\n✦ Fichiers texte\n✦ Très efficace",
            "Arithmétique": "✦ Probabilités\n✦ Haute compression\n✦ Textes naturels",
        }
        self._method_info.config(text=infos.get(self.method.get(), ""))

    # ────────────────────────────────────────────────────────
    #  UTILITAIRES
    # ────────────────────────────────────────────────────────

    @staticmethod
    def _fmt(size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        else:
            return f"{size_bytes/1024**2:.2f} MB"


# ══════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = Projet7Zip()
    app.mainloop()