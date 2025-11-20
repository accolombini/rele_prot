"""
Exportador de relatórios em formato Excel com formatação
"""
import pandas as pd
from pathlib import Path
from typing import Optional, Dict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from .base_reporter import BaseReporter


class ExcelReporter(BaseReporter):
    """Gera relatórios em formato Excel com formatação Petrobras"""
    
    def __init__(self, output_base_path: Optional[Path] = None):
        super().__init__(output_base_path)
        
        # Fontes
        self.header_font = Font(name='Arial', size=14, bold=True, color='FFFFFF')
        self.title_font = Font(name='Arial', size=11, bold=True, color='002366')
        self.data_font = Font(name='Arial', size=10)
        self.footer_font = Font(name='Arial', size=9, italic=True, color='666666')
        
        # Preenchimentos
        self.header_fill = PatternFill(start_color='002366', end_color='002366', fill_type='solid')
        self.title_fill = PatternFill(start_color='FFB81C', end_color='FFB81C', fill_type='solid')
        self.alt_row_fill = PatternFill(start_color='F0F0F0', end_color='F0F0F0', fill_type='solid')
        
        # Bordas
        thin_border = Side(style='thin', color='CCCCCC')
        self.border = Border(left=thin_border, right=thin_border, top=thin_border, bottom=thin_border)
        
        # Alinhamentos
        self.center_align = Alignment(horizontal='center', vertical='center')
        self.left_align = Alignment(horizontal='left', vertical='center')
    
    def export(
        self,
        df: pd.DataFrame,
        report_code: str,
        report_name: str,
        report_title: str,
        sheet_name: str = 'Relatório'
    ) -> Path:
        """
        Exporta DataFrame para Excel com formatação
        
        Args:
            df: DataFrame com os dados
            report_code: Código do relatório (ex: REL01)
            report_name: Nome descritivo (ex: fabricantes_reles)
            report_title: Título completo do relatório
            sheet_name: Nome da planilha
        
        Returns:
            Path do arquivo gerado
        """
        self.validate_dataframe(df)
        
        output_path = self.get_output_path(report_code, report_name, 'xlsx')
        
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name
        
        # Cabeçalho (linha 1)
        ws.merge_cells('A1:' + self._get_column_letter(len(df.columns)) + '1')
        header_cell = ws['A1']
        header_cell.value = f"{self.HEADER_SYMBOL}  {self.HEADER_TITLE}"
        header_cell.font = self.header_font
        header_cell.fill = self.header_fill
        header_cell.alignment = self.center_align
        ws.row_dimensions[1].height = 25
        
        # Título do relatório (linha 2)
        ws.merge_cells('A2:' + self._get_column_letter(len(df.columns)) + '2')
        title_cell = ws['A2']
        title_cell.value = report_title
        title_cell.font = self.title_font
        title_cell.alignment = self.center_align
        ws.row_dimensions[2].height = 20
        
        # Espaço (linha 3)
        ws.row_dimensions[3].height = 10
        
        # Dados (a partir da linha 4)
        start_row = 4
        
        # Cabeçalho dos dados
        for col_idx, column_name in enumerate(df.columns, 1):
            cell = ws.cell(row=start_row, column=col_idx)
            cell.value = column_name
            cell.font = Font(name='Arial', size=10, bold=True)
            cell.fill = self.title_fill
            cell.alignment = self.center_align
            cell.border = self.border
        
        # Linhas de dados
        for row_idx, row_data in enumerate(dataframe_to_rows(df, index=False, header=False), start_row + 1):
            for col_idx, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.value = value
                cell.font = self.data_font
                cell.alignment = self.left_align
                cell.border = self.border
                
                # Zebrar linhas
                if (row_idx - start_row) % 2 == 0:
                    cell.fill = self.alt_row_fill
        
        # Ajustar largura das colunas
        for col_idx, column_name in enumerate(df.columns, 1):
            max_length = max(
                len(str(column_name)),
                df[column_name].astype(str).str.len().max() if not df.empty else 10
            )
            ws.column_dimensions[self._get_column_letter(col_idx)].width = min(max_length + 3, 50)
        
        # Rodapé (última linha + 2)
        footer_row = ws.max_row + 2
        footer = self.format_footer_text(report_title)
        
        ws.merge_cells(f'A{footer_row}:' + self._get_column_letter(len(df.columns)) + f'{footer_row}')
        footer_cell = ws[f'A{footer_row}']
        footer_cell.value = f"{footer['left']} | {footer['center']} | {footer['right']}"
        footer_cell.font = self.footer_font
        footer_cell.alignment = self.center_align
        
        wb.save(output_path)
        return output_path
    
    def export_multiple_sheets(
        self,
        sheets: Dict[str, pd.DataFrame],
        report_code: str,
        report_name: str,
        report_title: str
    ) -> Path:
        """
        Exporta múltiplas planilhas em um único arquivo Excel
        
        Args:
            sheets: Dict onde chave=nome_sheet, valor=DataFrame
            report_code: Código do relatório
            report_name: Nome descritivo
            report_title: Título completo
        
        Returns:
            Path do arquivo gerado
        """
        output_path = self.get_output_path(report_code, report_name, 'xlsx')
        
        wb = Workbook()
        wb.remove(wb.active)  # Remove planilha padrão
        
        for sheet_name, df in sheets.items():
            ws = wb.create_sheet(title=sheet_name)
            
            # Aplicar mesma formatação
            self._format_sheet(ws, df, report_title)
        
        wb.save(output_path)
        return output_path
    
    def _format_sheet(self, ws, df: pd.DataFrame, report_title: str):
        """Aplica formatação a uma planilha"""
        # Cabeçalho
        ws.merge_cells('A1:' + self._get_column_letter(len(df.columns)) + '1')
        header_cell = ws['A1']
        header_cell.value = f"{self.HEADER_SYMBOL}  {self.HEADER_TITLE}"
        header_cell.font = self.header_font
        header_cell.fill = self.header_fill
        header_cell.alignment = self.center_align
        ws.row_dimensions[1].height = 25
        
        # Título
        ws.merge_cells('A2:' + self._get_column_letter(len(df.columns)) + '2')
        title_cell = ws['A2']
        title_cell.value = report_title
        title_cell.font = self.title_font
        title_cell.alignment = self.center_align
        ws.row_dimensions[2].height = 20
        
        ws.row_dimensions[3].height = 10
        
        # Dados
        start_row = 4
        for col_idx, column_name in enumerate(df.columns, 1):
            cell = ws.cell(row=start_row, column=col_idx)
            cell.value = column_name
            cell.font = Font(name='Arial', size=10, bold=True)
            cell.fill = self.title_fill
            cell.alignment = self.center_align
            cell.border = self.border
        
        for row_idx, row_data in enumerate(dataframe_to_rows(df, index=False, header=False), start_row + 1):
            for col_idx, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.value = value
                cell.font = self.data_font
                cell.alignment = self.left_align
                cell.border = self.border
                if (row_idx - start_row) % 2 == 0:
                    cell.fill = self.alt_row_fill
        
        # Ajustar colunas
        for col_idx, column_name in enumerate(df.columns, 1):
            max_length = max(
                len(str(column_name)),
                df[column_name].astype(str).str.len().max() if not df.empty else 10
            )
            ws.column_dimensions[self._get_column_letter(col_idx)].width = min(max_length + 3, 50)
        
        # Rodapé
        footer_row = ws.max_row + 2
        footer = self.format_footer_text(report_title)
        ws.merge_cells(f'A{footer_row}:' + self._get_column_letter(len(df.columns)) + f'{footer_row}')
        footer_cell = ws[f'A{footer_row}']
        footer_cell.value = f"{footer['left']} | {footer['center']} | {footer['right']}"
        footer_cell.font = self.footer_font
        footer_cell.alignment = self.center_align
    
    @staticmethod
    def _get_column_letter(col_idx: int) -> str:
        """Converte índice de coluna para letra (1=A, 27=AA)"""
        result = ""
        while col_idx > 0:
            col_idx -= 1
            result = chr(col_idx % 26 + 65) + result
            col_idx //= 26
        return result
