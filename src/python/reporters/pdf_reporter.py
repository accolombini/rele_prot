"""
Exportador de relatórios em formato PDF com cabeçalho e rodapé
"""
import pandas as pd
from pathlib import Path
from typing import Optional, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfgen import canvas
from .base_reporter import BaseReporter


class PDFReporter(BaseReporter):
    """Gera relatórios em formato PDF com formatação Petrobras"""
    
    def __init__(self, output_base_path: Optional[Path] = None):
        super().__init__(output_base_path)
        
        # Estilos
        self.styles = getSampleStyleSheet()
        
        # Estilo customizado para cabeçalho
        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#002366'),
            alignment=1,  # Center
            spaceAfter=12
        )
        
        # Estilo para título do relatório
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#002366'),
            alignment=1,
            spaceAfter=20
        )
    
    def export(
        self,
        df: pd.DataFrame,
        report_code: str,
        report_name: str,
        report_title: str,
        orientation: str = 'portrait'
    ) -> Path:
        """
        Exporta DataFrame para PDF com formatação
        
        Args:
            df: DataFrame com os dados
            report_code: Código do relatório (ex: REL01)
            report_name: Nome descritivo (ex: fabricantes_reles)
            report_title: Título completo do relatório
            orientation: 'portrait' ou 'landscape'
        
        Returns:
            Path do arquivo gerado
        """
        self.validate_dataframe(df)
        
        output_path = self.get_output_path(report_code, report_name, 'pdf')
        
        # Configurar página
        pagesize = landscape(A4) if orientation == 'landscape' else A4
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=pagesize,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=3*cm,
            bottomMargin=2.5*cm
        )
        
        # Container para elementos
        elements = []
        
        # Cabeçalho
        header_text = f"{self.HEADER_SYMBOL} {self.HEADER_TITLE}"
        header = Paragraph(header_text, self.header_style)
        elements.append(header)
        
        # Título do relatório
        title = Paragraph(report_title, self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        # Tabela de dados - converter para strings e limitar comprimento
        table_data = [df.columns.tolist()] + [
            [self._truncate_text(str(val), 80) for val in row] 
            for row in df.values.tolist()
        ]
        
        # Calcular larguras dinâmicas baseadas no conteúdo
        available_width = pagesize[0] - 4*cm
        col_widths = self._calculate_column_widths(df, available_width)
        
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Estilo da tabela
        table_style = TableStyle([
            # Cabeçalho
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFB81C')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#002366')),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Dados
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),  # Alinhamento vertical no topo
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),  # Reduzido para 8pt
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('LEFTPADDING', (0, 1), (-1, -1), 4),
            ('RIGHTPADDING', (0, 1), (-1, -1), 4),
            ('WORDWRAP', (0, 1), (-1, -1), True),  # Quebra de texto automática
            
            # Linhas alternadas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),
            
            # Bordas
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#002366')),
        ])
        
        table.setStyle(table_style)
        elements.append(table)
        
        # Construir PDF com rodapé customizado
        doc.build(
            elements,
            onFirstPage=lambda canvas, doc: self._add_footer(canvas, doc, report_title, 1),
            onLaterPages=lambda canvas, doc: self._add_footer(canvas, doc, report_title, doc.page)
        )
        
        return output_path
    
    def export_multiple_tables(
        self,
        tables: List[tuple],
        report_code: str,
        report_name: str,
        report_title: str,
        orientation: str = 'portrait'
    ) -> Path:
        """
        Exporta múltiplas tabelas em um único PDF
        
        Args:
            tables: Lista de tuplas (section_title, DataFrame)
            report_code: Código do relatório
            report_name: Nome descritivo
            report_title: Título completo
            orientation: 'portrait' ou 'landscape'
        
        Returns:
            Path do arquivo gerado
        """
        output_path = self.get_output_path(report_code, report_name, 'pdf')
        
        pagesize = landscape(A4) if orientation == 'landscape' else A4
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=pagesize,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=3*cm,
            bottomMargin=2.5*cm
        )
        
        elements = []
        
        # Cabeçalho principal
        header_text = f"{self.HEADER_SYMBOL} {self.HEADER_TITLE}"
        header = Paragraph(header_text, self.header_style)
        elements.append(header)
        
        title = Paragraph(report_title, self.title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))
        
        # Adicionar cada tabela
        for i, (section_title, df) in enumerate(tables):
            if i > 0:
                elements.append(PageBreak())
            
            # Título da seção
            section_style = ParagraphStyle(
                'SectionTitle',
                parent=self.styles['Heading3'],
                fontSize=11,
                textColor=colors.HexColor('#002366'),
                spaceAfter=10
            )
            section = Paragraph(section_title, section_style)
            elements.append(section)
            
            # Tabela
            table_data = [df.columns.tolist()] + df.values.tolist()
            available_width = pagesize[0] - 4*cm
            col_widths = [available_width / len(df.columns)] * len(df.columns)
            
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFB81C')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#002366')),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#002366')),
            ])
            
            table.setStyle(table_style)
            elements.append(table)
            elements.append(Spacer(1, 1*cm))
        
        doc.build(
            elements,
            onFirstPage=lambda canvas, doc: self._add_footer(canvas, doc, report_title, 1),
            onLaterPages=lambda canvas, doc: self._add_footer(canvas, doc, report_title, doc.page)
        )
        
        return output_path
    
    def _add_footer(self, canvas: canvas.Canvas, doc, report_title: str, page_num: int):
        """Adiciona rodapé em cada página"""
        canvas.saveState()
        
        footer = self.format_footer_text(report_title, page_num)
        
        # Linha separadora
        canvas.setStrokeColor(colors.HexColor('#CCCCCC'))
        canvas.setLineWidth(0.5)
        canvas.line(2*cm, 2*cm, doc.pagesize[0] - 2*cm, 2*cm)
        
        # Texto do rodapé
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor('#666666'))
        
        # Esquerda
        canvas.drawString(2*cm, 1.5*cm, footer['left'])
        
        # Centro
        text_width = canvas.stringWidth(footer['center'], 'Helvetica', 9)
        canvas.drawString((doc.pagesize[0] - text_width) / 2, 1.5*cm, footer['center'])
        
        # Direita
        text_width = canvas.stringWidth(footer['right'], 'Helvetica', 9)
        canvas.drawString(doc.pagesize[0] - 2*cm - text_width, 1.5*cm, footer['right'])
        
        canvas.restoreState()
    
    def _calculate_column_widths(self, df: pd.DataFrame, available_width: float) -> list:
        """
        Calcula larguras dinâmicas das colunas baseadas no conteúdo
        
        Estratégia:
        1. Analisa comprimento máximo de cada coluna (header + dados)
        2. Distribui largura proporcionalmente
        3. Garante mínimo de 2cm e máximo de 8cm por coluna
        """
        if df.empty or len(df.columns) == 0:
            return [available_width]
        
        # Calcular comprimento máximo de cada coluna
        col_lengths = []
        for col in df.columns:
            # Comprimento do header
            header_len = len(str(col))
            # Comprimento máximo dos dados (limitado a 80 chars)
            data_len = df[col].astype(str).str.len().max() if not df.empty else 10
            data_len = min(data_len, 80)  # Limite para evitar colunas muito largas
            col_lengths.append(max(header_len, data_len))
        
        # Calcular pesos proporcionais
        total_chars = sum(col_lengths)
        if total_chars == 0:
            # Fallback: distribuir igualmente
            return [available_width / len(df.columns)] * len(df.columns)
        
        # Distribuir largura proporcionalmente aos caracteres
        col_widths = [(length / total_chars) * available_width for length in col_lengths]
        
        # Aplicar limites: mínimo 2cm, máximo 8cm
        min_width = 2 * cm
        max_width = 8 * cm
        col_widths = [max(min_width, min(w, max_width)) for w in col_widths]
        
        # Ajustar se total exceder disponível
        total_width = sum(col_widths)
        if total_width > available_width:
            # Reduzir proporcionalmente
            scale_factor = available_width / total_width
            col_widths = [w * scale_factor for w in col_widths]
        
        return col_widths
    
    @staticmethod
    def _truncate_text(text: str, max_length: int = 80) -> str:
        """
        Trunca texto longo e adiciona reticências
        """
        text = str(text).strip()
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + '...'
