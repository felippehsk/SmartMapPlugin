# Smart-Map

**Compatible with QGIS 3.10+ and QGIS 4** (tested on QGIS 4.2 / Windows 11).

Open-source QGIS plugin for soil attribute prediction and mapping. It supports:

- Ordinary Kriging interpolation
- Machine Learning with Support Vector Machine (SVM)
- Management zone generation
- Interaction with QGIS layers (Shapefile, GeoTIFF, and related formats)

Built in Python 3. Runtime libraries such as [scikit-learn](https://github.com/scikit-learn/scikit-learn), [scikit-fuzzy](https://github.com/scikit-fuzzy/scikit-fuzzy), and [pysal](https://github.com/pysal) are either bundled or installed automatically on first load.

---

## Cite this software

Pereira, G.W.; Valente, D.S.M.; Queiroz, D.M.d.; Coelho, A.L.d.F.; Costa, M.M.; Grift, T. [Smart-Map: An Open-Source QGIS Plugin for Digital Mapping Using Machine Learning Techniques and Ordinary Kriging. Agronomy 2022, 12, 1350.](https://www.mdpi.com/2073-4395/12/6/1350/htm) https://doi.org/10.3390/agronomy12061350

---

## Install (recommended)

### Install from ZIP (QGIS 3 or QGIS 4)

1. Download **`Smart_Map.zip`** from the latest [GitHub Release](https://github.com/felippehsk/SmartMapPlugin/releases).
2. In QGIS open **Plugins → Manage and Install Plugins → Install from ZIP**.
3. Select `Smart_Map.zip` and install.
4. Enable **Smart-Map** in the plugin list.
5. Restart QGIS if prompted after dependency installation.

On first load, missing Python packages (for example `scikit-learn`) are installed automatically into the writable QGIS user profile. The Windows QGIS 4 package includes offline wheels for Python 3.12.

### Plugin repository

You can also search for **Smart-Map** in **Plugins → Manage and Install Plugins → All** when the plugin is published in the official QGIS plugin repository.

---

## Dependencies

**Requirements:** QGIS **3.10 or newer**, including **QGIS 4.x**, 64-bit.

| Package | Notes |
|---------|--------|
| numpy, scipy, pandas, matplotlib | Usually already included with QGIS |
| scikit-learn | Auto-installed on first load (bundled wheels on Windows QGIS 4) |
| skfuzzy / pysal pieces | Vendored with the plugin |

### If automatic install fails

#### Windows

Open **OSGeo4W Shell** / QGIS command prompt and run:

```bat
python-qgis.bat -m pip install scikit-learn
```

If you see `PermissionError`, run the shell as Administrator, or install into the user profile (the plugin’s auto-installer already prefers a writable user folder).

#### Linux / macOS

In the QGIS Python Console, check:

```python
import pandas
import scipy
import sklearn
```

If any import fails, install with the same Python used by QGIS, for example:

```bash
python3 -m pip install --user scikit-learn pandas scipy
```

---

## User guide

Simplified tutorial: [Wiki](https://github.com/gustavowillam/SmartMapPlugin/wiki)

---

## Report bugs

When reporting an issue, please include:

1. The full Python error dialog text (if shown)
2. Logs from the QGIS Log Messages panel (`Python Error` and `Smart-Map` tabs)
3. Exact steps to reproduce, and whether restarting/reinstalling changes the result
4. What happened vs what you expected
5. A sample project/layers if possible

Open an issue at: [Issues](https://github.com/felippehsk/SmartMapPlugin/issues)

---

## QGIS downloads

- [QGIS for Windows](https://qgis.org/download/)
- [QGIS for Linux / macOS / other](https://qgis.org/download/)

---

## Documentation / APIs

- [Python](https://www.python.org/)
- [Qt documentation](https://doc.qt.io/)
- [PyQGIS API](https://qgis.org/pyqgis/)
- [PyQGIS developer cookbook](https://docs.qgis.org/latest/en/docs/pyqgis_developer_cookbook/index.html)

---

## License (GPL-3.0)

This program is free software; you can redistribute it and/or modify it under the terms of the [GNU General Public License](https://www.gnu.org/licenses/gpl-3.0.html) as published by the Free Software Foundation; either version 3 of the License, or (at your option) any later version.

---

# Smart-Map (Português)

**Compatível com QGIS 3.10+ e QGIS 4** (testado no QGIS 4.2 / Windows 11).

Plugin open source para QGIS voltado à predição e ao mapeamento de atributos do solo. Permite:

- Interpolação por Krigagem Ordinária
- Machine Learning com Support Vector Machine (SVM)
- Geração de zonas de manejo
- Integração com layers do QGIS (Shapefile, GeoTIFF e formatos relacionados)

Desenvolvido em Python 3. Bibliotecas como [scikit-learn](https://github.com/scikit-learn/scikit-learn), [scikit-fuzzy](https://github.com/scikit-fuzzy/scikit-fuzzy) e [pysal](https://github.com/pysal) vêm embutidas ou são instaladas automaticamente na primeira execução.

## Como citar

Pereira, G.W.; Valente, D.S.M.; Queiroz, D.M.d.; Coelho, A.L.d.F.; Costa, M.M.; Grift, T. [Smart-Map: An Open-Source QGIS Plugin for Digital Mapping Using Machine Learning Techniques and Ordinary Kriging. Agronomy 2022, 12, 1350.](https://www.mdpi.com/2073-4395/12/6/1350/htm) https://doi.org/10.3390/agronomy12061350

## Instalação (recomendada)

### Instalar a partir de ZIP (QGIS 3 ou QGIS 4)

1. Baixe o arquivo **`Smart_Map.zip`** na página de [Releases](https://github.com/felippehsk/SmartMapPlugin/releases).
2. No QGIS, abra **Plugins → Gerenciar e Instalar Complementos → Instalar a partir de ZIP**.
3. Selecione `Smart_Map.zip` e instale.
4. Ative o complemento **Smart-Map**.
5. Reinicie o QGIS se for solicitado após a instalação de dependências.

Na primeira execução, pacotes Python ausentes (por exemplo `scikit-learn`) são instalados automaticamente no perfil do usuário do QGIS. O pacote para Windows / QGIS 4 inclui wheels offline para Python 3.12.

### Repositório de plugins

Também é possível buscar por **Smart-Map** em **Plugins → Gerenciar e Instalar Complementos → Todos**, quando o plugin estiver publicado no repositório oficial do QGIS.

## Dependências

**Requisito:** QGIS **3.10 ou superior**, incluindo **QGIS 4.x**, 64 bits.

Se a instalação automática falhar no Windows, abra o **OSGeo4W Shell** / prompt do QGIS e execute:

```bat
python-qgis.bat -m pip install scikit-learn
```

No Linux/macOS, confira no Console Python do QGIS se `pandas`, `scipy` e `sklearn` importam corretamente e, se necessário, instale-os com o Python do próprio QGIS.

## Manual de utilização

Tutorial simplificado: [Wiki](https://github.com/gustavowillam/SmartMapPlugin/wiki)

## Reportar erros

Inclua a mensagem completa de erro Python, os logs do painel de mensagens do QGIS (abas `Python Error` e `Smart-Map`), os passos para reproduzir o problema e, se possível, um projeto de exemplo.

Abra uma issue em: [Issues](https://github.com/felippehsk/SmartMapPlugin/issues)

## Licença (GPL-3.0)

Este programa é software livre; você pode redistribuí-lo e/ou modificá-lo sob os termos da [GNU General Public License](https://www.gnu.org/licenses/gpl-3.0.pt-br.html) da Free Software Foundation; versão 3 da Licença, ou (a seu critério) qualquer versão posterior.
