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
    for (plate, assay), subdf in df.groupby(['plate', 'assay']):
        table = ET.SubElement(root, 'Table', ID=f"Tbl_{plate}_{assay}", XFormat="none", YFormat="replicates", TableType="TwoWay")
        max_replicates_in_table = 0
        ET.SubElement(table, 'Title').text = f"{plate}_{assay}"

        # Filas: horas ordenadas
        hours = sorted(subdf['hour'].unique())
        rowcol = ET.SubElement(table, 'RowTitlesColumn')
        subcol = ET.SubElement(rowcol, 'Subcolumn')
        for h in hours:
            ET.SubElement(subcol, 'd').text = str(h)

        # Cada dosis real
        for real_dose, grp in subdf.groupby('real_dose'):
            # Precompute list of values per hour (preserve order)
            hour_values = {h: grp[grp['hour'] == h]['value'].tolist() for h in hours}
            # Número de réplicas = máximo número de valores en cualquier hora
            replicates = max((len(vs) for vs in hour_values.values()), default=0)
            max_replicates_in_table = max(max_replicates_in_table, replicates)
            ycol = ET.SubElement(table, 'YColumn', Subcolumns=str(replicates))
            ET.SubElement(ycol, 'Title').text = str(real_dose)

            # Crear un Subcolumn por réplica
            for r in range(replicates):
                sub = ET.SubElement(ycol, 'Subcolumn')
                # Añadir un valor por cada hora (o vacío si esta réplica no existe para esa hora)
                for h in hours:
                    vals = hour_values[h]
                    if r < len(vals):
                        ET.SubElement(sub, 'd').text = str(vals[r])
                    else:
                        ET.SubElement(sub, 'd')
        # Añadir atributo Replicates al <Table>
        table.set('Replicates', str(max_replicates_in_table))

    # Prettify y escribir
    xml_str = ET.tostring(root, encoding='utf-8')
    parsed = minidom.parseString(xml_str)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(parsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8'))
