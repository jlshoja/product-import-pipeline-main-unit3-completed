# FILE\_DEPENDENCIES

archive\_urls.xlsx
Producer: User
Consumer: product\_extraction

extracted\_products.xlsx
Producer: link\_scraper.py
Consumer: spec\_scraper.py

product\_details\_complete.xlsx
Producer: spec\_scraper.py
Consumer: downstream modules



\# Hardcoded Path and File Dependency Analysis



\## Overview



Phase 4 identified a significant number of hardcoded paths, folder names, filenames, and repository structure assumptions throughout the codebase.



These dependencies increase migration risk because modules depend on specific filesystem layouts rather than centralized configuration.



\---



\# High-Risk File Dependencies



| Dependency                    | Type              | Used By                                                      | Risk   |

| ----------------------------- | ----------------- | ------------------------------------------------------------ | ------ |

| archive\_urls.xlsx             | Input File        | link\_scraper.py, main.py                                     | High   |

| extracted\_products.xlsx       | Intermediate File | link\_scraper.py, spec\_scraper.py, image\_processing, trackers | High   |

| product\_details\_complete.xlsx | Output File       | spec\_scraper.py                                              | High   |

| product\_tracking\_LATEST.xlsx  | Tracking File     | price\_tracker.py                                             | High   |

| color\_mapping.xlsx            | Mapping File      | product\_extraction, import\_builder                           | High   |

| product\_names.xlsx            | Mapping File      | import\_builder                                               | High   |

| checkpoint.xlsx               | Recovery File     | link\_scraper.py                                              | High   |

| scraper\_progress.json         | State File        | spec\_scraper.py                                              | High   |

| link\_scraper\_progress.json    | State File        | link\_scraper.py                                              | High   |

| download\_state.json           | State File        | image\_processing                                             | Medium |

| price\_history.xlsx            | History File      | history subsystem                                            | Medium |



\---



\# Hardcoded Folder Dependencies



| Folder            | Used By                                                          | Risk   |

| ----------------- | ---------------------------------------------------------------- | ------ |

| uploads           | web\_panel\_v12.py, woocommerce\_generator\_v12.py, compare\_scans.py | High   |

| product-images    | woocommerce\_generator\_v12.py, image processing workflow          | High   |

| runtime/reports   | spec\_scraper.py, dashboard\_generator.py, compare\_scans.py        | Medium |

| assets/templates  | dashboard subsystem                                              | Medium |

| runtime/reports   | dashboard subsystem                                              | Medium |

| runtime/logs      | settings.py, import\_builder                                      | Medium |

| data/             | settings.py, paths.py                                            | Medium |



\---



\# Repository Layout Assumptions



The following relative paths assume a fixed repository structure:



```text

../../4\_Product\_import/uploads

../4\_Product\_import/uploads

../uploads

../runtime/reports

```



Affected Modules:



\* compare\_scans.py

\* woocommerce\_generator\_v12.py



Risk Level:



Very High



Reason:



Migration, restructuring, or relocation of modules may immediately break these references.



Recommended Future State:



All directory access should occur through a centralized configuration registry.



\---



\# Mapping File Dependencies



\## Color Mapping



Current Locations:



\* product\_extraction/color\_mapping.xlsx

\* import\_builder/color\_mapping.xlsx

Unit 6 Status:

\* Product extraction color helper logic was partially consolidated in `product_extraction/common/color_utils.py`.

\* Approved product extraction color consumers now share normalization, fallback slugging, splitting, and de-duplication helpers.

\* Mapping file sources were not consolidated in Unit 6.

\* `import_builder/` remains deferred and must not be modified without explicit approval.



Risk:



High



Issue:



Duplicate mapping sources may diverge.



Recommendation:



Single shared configuration source.



\---



\## Product Naming Mapping



Current Location:



\* import\_builder/product\_names.xlsx



Risk:



High



Issue:



Critical dependency for WooCommerce output generation.



Recommendation:



Move to centralized configuration repository.



\---



\# Environment Dependencies



\## SECRET\_KEY



Consumer:



\* web\_panel\_v12.py



Risk:



High



Issue:



Environment configuration is not centralized.



Recommendation:



Central environment configuration loader.



\---



\# Migration Recommendations



Priority 1



\* Centralize filenames.

\* Centralize directory definitions.

\* Eliminate relative path traversal dependencies.



Priority 2



\* Consolidate color mapping files.

\* Consolidate product naming configuration.



Priority 3



\* Introduce shared configuration registry.

\* Remove direct filename references from modules.



\---



\# Migration Readiness Impact



Current State:



Moderate–High configuration coupling.



Key Risks:



\* Hardcoded filenames.

\* Hardcoded directory paths.

\* Relative repository layout assumptions.

\* Duplicate configuration files.



Recommendation:



Configuration centralization should be completed before major architectural migration activities begin.


