\# Configuration Inventory Report



\## Executive Summary



Configuration management is currently distributed across:



\* Excel-based configuration files

\* Python settings modules

\* Hardcoded constants

\* Environment variables

\* Path definitions embedded in application code



The repository contains multiple independent configuration mechanisms with significant duplication.



Overall Risk Assessment: \*\*Medium–High\*\*



\---



\# Configuration Sources



\## 1. data\_standardization/standar\_colors.xlsx



\### Location



data\_standardization/standar\_colors.xlsx



\### Type



Excel Configuration



\### Owning Module



data\_standardization



\### Consumers



\* Category/color standardization processes



\### Purpose



Canonical color normalization dataset.



\### Migration Priority



High



\### Risk Level



Medium



\---



\## 2. data\_standardization/standard\_categories.xlsx



\### Location



data\_standardization/standard\_categories.xlsx



\### Type



Excel Configuration



\### Owning Module



data\_standardization



\### Consumers



\* Product categorization workflow



\### Purpose



Category mapping and normalization.



\### Migration Priority



High



\### Risk Level



Medium



\---



\## 3. data\_standardization/pricing\_sample.xlsx



\### Location



data\_standardization/pricing\_sample.xlsx



\### Type



Pricing Configuration



\### Owning Module



data\_standardization



\### Consumers



Pricing normalization workflow.



\### Purpose



Pricing transformation reference.



\### Migration Priority



Medium



\### Risk Level



Low



\---



\## 4. data/reference/word index.xlsx



\### Location



data/reference/word index.xlsx



\### Type



Lookup / Mapping Configuration



\### Owning Module



data\_standardization



\### Consumers



Text standardization workflow.



\### Purpose



Keyword normalization and indexing.



\### Migration Priority



Medium



\### Risk Level



Low



\---



\## 5. import\_builder/color\_mapping.xlsx



\### Location



import\_builder/color\_mapping.xlsx



\### Type



Color Mapping Configuration



\### Owning Module



import\_builder



\### Consumers



\* color\_manager.py

\* image\_naming\_v11\_fixed.py

\* woocommerce\_generator\_v12.py

\* web\_panel\_v12.py

\* color\_similarity.py



\### Purpose



Maps extracted colors to approved WooCommerce colors.



\### Migration Priority



Critical



\### Risk Level



High



\---



\## 6. product\_extraction/color\_mapping.xlsx



\### Location



product\_extraction/color\_mapping.xlsx



\### Type



Color Mapping Configuration



\### Owning Module



product\_extraction



\### Consumers



\* color\_manager.py

\* utils/color\_manager.py

\* spec\_scraper.py



\### Purpose



Color normalization during extraction.



\### Migration Priority



Critical



\### Risk Level



High



\### Notes



Duplicate configuration exists in another module.



\---



\## 7. import\_builder/product\_names.xlsx



\### Location



import\_builder/product\_names.xlsx



\### Type



Product Naming Configuration



\### Owning Module



import\_builder



\### Consumers



\* product\_name\_manager.py

\* woocommerce\_generator\_v12.py

\* web\_panel\_v12.py



\### Purpose



Manual overrides and approved product naming.



\### Migration Priority



Critical



\### Risk Level



High



\---



\# Python Configuration Files



\## 8. product\_extraction/config/settings.py



\### Location



product\_extraction/config/settings.py



\### Type



Application Settings



\### Owning Module



product\_extraction



\### Consumers



Most extraction components.



\### Purpose



Central extraction configuration.



\### Migration Priority



Critical



\### Risk Level



High



\### Notable Values



\* archive\_urls.xlsx

\* extracted\_products.xlsx

\* product\_details\_complete.xlsx

\* color\_mapping.xlsx

\* product\_tracking\_LATEST.xlsx



\---



\## 9. product\_extraction/config/history\_config.py



\### Location



product\_extraction/config/history\_config.py



\### Type



History Configuration



\### Owning Module



product\_extraction



\### Consumers



price\_history\_manager.py



\### Purpose



Price history retention and archive behavior.



\### Migration Priority



High



\### Risk Level



Medium



\### Notable Values



\* price\_history.xlsx



\---



\## 10. import\_builder/config\_v9.py



\### Location



import\_builder/config\_v9.py



\### Type



Legacy Settings



\### Owning Module



import\_builder



\### Consumers



Legacy import builder workflow.



\### Purpose



Historical configuration layer.



\### Migration Priority



High



\### Risk Level



High



\---



\## 11. import\_builder/paths.py



\### Location



import\_builder/paths.py



\### Type



Path Configuration



\### Owning Module



import\_builder



\### Consumers



Multiple builder modules.



\### Purpose



Centralized path definitions.



\### Migration Priority



Critical



\### Risk Level



Medium



\---



\# Environment Configuration



\## 12. Environment Variables



\### SECRET\_KEY



\### Consumers



Flask application.



\### Purpose



Session security.



\### Migration Priority



Critical



\### Risk Level



High



\---



\# Hardcoded Configuration Inventory



\## Extraction Pipeline



\### link\_scraper.py



Hardcoded:



\* archive\_urls.xlsx

\* extracted\_products.xlsx

\* checkpoint.xlsx



Risk: High



\---



\### spec\_scraper.py



Hardcoded:



\* extracted\_products.xlsx

\* product\_details\_complete.xlsx

\* color\_mapping.xlsx



Risk: High



\---



\### price\_tracker.py



Hardcoded:



\* extracted\_products.xlsx

\* product\_tracking\_LATEST.xlsx



Risk: Medium



\---



\### compare\_scans.py



Hardcoded:



\* reports folder names

\* uploads folder names

\* output naming conventions



Risk: Medium



\---



\## Import Builder



\### woocommerce\_generator\_v12.py



Hardcoded:



\* color\_mapping.xlsx

\* product\_names.xlsx



Risk: High



\---



\### image\_naming\_v11\_fixed.py



Hardcoded:



\* color\_mapping.xlsx



Risk: Medium



\---



\### web\_panel\_v12.py



Hardcoded:



\* color\_mapping.xlsx

\* product\_names.xlsx



Risk: High



\---



\### ai\_description\_generator.py



Hardcoded:



\* products.xlsx



Risk: Medium



\---



\## Image Processing



\### Image\_Downloader.py



Hardcoded:



\* extracted\_products.xlsx



Risk: Medium



\---



\### menu.py



Hardcoded:



\* extracted\_products.xlsx



Risk: Medium



\---



\# Missing Configurations



The following values appear hardcoded but should be externalized:



1\. Input filenames

2\. Output filenames

3\. Report filenames

4\. Upload directory names

5\. Archive directory names

6\. Checkpoint filenames

7\. CSV export filenames

8\. WooCommerce output filenames

9\. Product tracking filenames

10\. Snapshot filenames



Recommended destination:



config.yaml



or



central settings module



\---



\# Duplicate Configurations



\## Duplicate Color Mapping



Locations:



\* import\_builder/color\_mapping.xlsx

\* product\_extraction/color\_mapping.xlsx



Risk:



High



Reason:



Mappings may diverge over time.



Recommendation:



Single shared source.



\---



\## Duplicate Color Management Logic



Locations:



\* import\_builder/color\_manager.py

\* product\_extraction/color\_manager.py

\* product\_extraction/utils/color\_manager.py



Risk:



High



Recommendation:



Consolidate into shared library.



\---



\## Duplicate Path Definitions



Observed across:



\* settings.py

\* paths.py

\* individual scripts



Risk:



Medium



Recommendation:



Central configuration registry.



\---



\# High-Risk Configurations



\## Color Mapping



Files:



\* import\_builder/color\_mapping.xlsx

\* product\_extraction/color\_mapping.xlsx



Reason:



Impacts extraction and import generation.



\---



\## Product Naming Rules



File:



\* import\_builder/product\_names.xlsx



Reason:



Directly affects generated WooCommerce catalog.



\---



\## settings.py



Reason:



Primary extraction configuration source.



\---



\## Environment Secret Key



Reason:



Required for Flask security.



\---



\# Recommended Consolidation Candidates



\## Priority 1



Central Configuration Package



Create:



config/



Containing:



\* paths.py

\* filenames.py

\* environment.py

\* application.py



\---



\## Priority 2



Shared Mapping Repository



Move:



\* color\_mapping.xlsx

\* product\_names.xlsx

\* standard\_categories.xlsx

\* standar\_colors.xlsx



Into:



shared\_config/



\---



\## Priority 3



Single Color Manager



Replace:



\* import\_builder/color\_manager.py

\* product\_extraction/color\_manager.py

\* product\_extraction/utils/color\_manager.py



With:



shared/color\_manager.py



\---



\## Priority 4



Central File Naming Policy



Externalize:



\* archive\_urls.xlsx

\* extracted\_products.xlsx

\* product\_details\_complete.xlsx

\* checkpoint.xlsx

\* product\_tracking\_LATEST.xlsx



Into configuration layer.



\---



\# Overall Assessment



Configuration Maturity: Moderate



Key Findings:



\* Configuration is partially centralized.

\* Significant reliance on hardcoded filenames remains.

\* Duplicate mapping files exist.

\* Color-management configuration is fragmented.

\* Migration should prioritize configuration consolidation before major architectural changes.



Migration Readiness Impact:



Current configuration architecture introduces avoidable migration risk and should be addressed early in the migration program.


