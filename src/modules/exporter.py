"""
Module for data exporting functionalities.
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom
import pandas as pd

def df_to_graphpad_xml(df: pd.DataFrame, output_file: str):
    """
    Convierte un DataFrame con columnas:
      date, hour, plate, x, y, assay, theo_dose, real_dose, value
    en un archivo XML de GraphPad Prism.

    Cada combinación plate+assay genera una <Table>:
      - Title = plate + assay
      - RowTitlesColumn = horas
      - Un <YColumn> por cada real_dose única
      - En cada YColumn, un <Subcolumn> por grupo de valores (date,hour,plate,assay,real_dose)
    """
    # Espacios de nombres
    ns = {'ps': 'http://graphpad.com/prism/Prism.htm'}
    ET.register_namespace('', ns['ps'])

    # Raíz y cabecera
    root = ET.Element('GraphPadPrismFile', nsmap=ns)
    created = ET.SubElement(root, 'Created')
    # Metadatos mínimos
    ET.SubElement(created, 'OriginalVersion', CreatedByProgram="PythonScript", CreatedByVersion="1.0", Login="", DateTime=pd.Timestamp.now().isoformat())

    # Agrupar por fecha y tabla
    for (date, plate, assay), subdf in df.groupby(['date', 'plate', 'assay']):
        table = ET.SubElement(root, 'Table', ID=f"Tbl_{plate}_{assay}", XFormat="none", YFormat="replicates", TableType="TwoWay")
        ET.SubElement(table, 'Title').text = f"{plate}_{assay}"

        # Filas: horas ordenadas
        hours = sorted(subdf['hour'].unique())
        rowcol = ET.SubElement(table, 'RowTitlesColumn')
        subcol = ET.SubElement(rowcol, 'Subcolumn')
        for h in hours:
            ET.SubElement(subcol, 'd').text = str(h)

        # Cada dosis real
        for real_dose, grp in subdf.groupby('real_dose'):
            # Precompute lists of values per hour
            hour_values = {h: grp[grp['hour'] == h]['value'].tolist() for h in hours}
            max_len = max((len(vs) for vs in hour_values.values()), default=0)
            ycol = ET.SubElement(table, 'YColumn', Subcolumns=str(max_len))
            ET.SubElement(ycol, 'Title').text = str(real_dose)
            # Para cada hora, crear un Subcolumn con exactamente max_len <d>
            for h in hours:
                vals = hour_values[h]
                sub = ET.SubElement(ycol, 'Subcolumn')
                # Rellenar con valores y, si faltan, con <d/> vacíos
                for v in vals:
                    ET.SubElement(sub, 'd').text = str(v)
                for _ in range(max_len - len(vals)):
                    ET.SubElement(sub, 'd')
    
    # Prettify y escribir
    xml_str = ET.tostring(root, encoding='utf-8')
    parsed = minidom.parseString(xml_str)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(parsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8'))
