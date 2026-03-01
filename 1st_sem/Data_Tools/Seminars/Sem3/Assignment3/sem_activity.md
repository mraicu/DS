# KarstCave_FormationData_2024 – Dataset Metadata

## **Title of Dataset**

**KarstCave_FormationData_2024**

This dataset contains mineral composition, formation type, and environmental measurements from 150 rock samples collected in the Postojna Cave System (Slovenia) between March and July 2024.

## **Principal Contacts**

### **Principal Investigator (PI)**

**Dr. Ana Kovač**  
Karst Research Institute, Slovenia

### **Data Manager / Custodian**

**Luka Marin**  
Karst Research Institute, Slovenia

## **File Name Structure**

### **Structure**

`KCFS_YYYYMMDD_SampleID.ext`

### **Attributes**

-   **KCFS** — Karst Cave Formation Study prefix
-   **YYYYMMDD** — Collection date
-   **SampleID** — Unique identifier (e.g., S034)
-   **ext** — File extension (CSV, PNG, PDF, etc.)

### **Codes / Abbreviations**

| Code | Meaning                    |
| ---- | -------------------------- |
| KCFS | Karst Cave Formation Study |
| S### | Sample number (001–150)    |
| XRD  | X-ray Diffraction report   |
| ENV  | Environmental record       |
| IMG  | Image file                 |

### **Examples**

-   `KCFS_20240512_S034.csv`
-   `KCFS_20240701_S112_IMG.png`
-   `KCFS_20240328_S005_XRD.pdf`

## **File Formats**

### Present in Dataset

-   **CSV** — Primary tabular data
-   **XML** — Metadata exports
-   **PNG**, **JPEG** — Sample images
-   **PDF/A** — XRD reports
-   **TXT (UTF-8)** — Field notes

### Notes on Conversions

If converting between formats:

-   Maintain decimal precision
-   Avoid lossy compression for images
-   Preserve metadata (timestamps, EXIF)

## **Column Headings for Tabular Data**

| Column Name             | Type        | Description                                                 | Units / Format  |
| ----------------------- | ----------- | ----------------------------------------------------------- | --------------- |
| **Sample_ID**           | String      | Unique code identifying sample                              | –               |
| **GPS_Latitude**        | Float       | Latitude of sampling point                                  | Decimal degrees |
| **GPS_Longitude**       | Float       | Longitude of sampling point                                 | Decimal degrees |
| **Formation_Type**      | Categorical | Speleothem type (stalactite, stalagmite, column, flowstone) | –               |
| **Mineral_Composition** | String      | Minerals identified via XRD (calcite, aragonite, etc.)      | –               |
| **Moisture_Level**      | Float       | Relative humidity at sampling site                          | %               |
| **Temperature**         | Float       | Cave air temperature                                        | °C              |
| **Collection_Date**     | Date        | Sample collection date                                      | YYYY-MM-DD      |

### Additional Data Notes

-   Missing data is coded as **NA**
-   Mineral lists are comma-separated strings
-   Formation types restricted to defined categories

## **Units of Measurement**

-   Moisture: **%**
-   Temperature: **°C**
-   Coordinates: **WGS84 decimal degrees**

## **Calculations**

-   All environmental values are directly measured
-   GPS coordinates captured in-field without post-processing

## **Versioning & Change Tracking**

### Versioning Scheme

`vMajor.Minor.Patch`

### Changelog

-   **v1.0.0 (2024-08-01)** — Initial dataset release
-   **v1.1.0 (2024-08-10)** — Corrected GPS coordinates for S045–S048
-   **v1.1.1 (2024-08-12)** — Updated mineral composition format rules
