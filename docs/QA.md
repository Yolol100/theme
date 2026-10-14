# Webactueel Starter — QA en bewijsgrenzen

**Eindstatus: SOURCE REVIEWED / STAGING REQUIRED; geen 10/10 en geen productie-GO.**

## Herkomst

- Aangeleverde en geverifieerde bron: `Webactueel-Universal-Theme-1.0.4.zip`, SHA-256 `852799b7d6ff78303f22e7b4a77447b305955c45017f18ab0dcecab3bcc245ef`, 59 bestanden.
- `Webactueel-Universal-Theme-1.0.4-source-derived.zip`, SHA-256 `ed1918a04f1695ebc28b3e83c1b9c539fb9663021c034ba762f1bc005ef9dc90`, dezelfde themabestanden. Afgeleid bronpakket, geen oorspronkelijke CI/git-historie.
- De bron is alleen als referentie geïnventariseerd; dit nieuwe **starterthema** heeft een andere slug. Geen stille vervanging van bestaande sites.

## Scopeverschil

Bewust niet meegenomen uit het multipurpose-thema: 25 automatisch geregistreerde patronen, 2 conditionele shop-patronen, alle meta-velden, editor-sidebar, PHP-bootstrap, WooCommerce-hooks, 4 stijlvarianten, CSS/JS-bundels, branche- en voorbeeldteksten en specifieke page templates. Deze onderdelen zijn voor een lege boilerplate onnodig; het verwijderen op een bestaande site zou niet zomaar veilig zijn.

## Statische controles

De repository bevat `tests/test_starter.py` dat per route blok-commentaarparen, JSON-attributen, templateverwijzingen, hoofdelement, queryverloop, minimale bestanden, contrastwaarden, responsieve Core-layoutkenmerken en afwezigheid van dynamische code/onnodige afhankelijkheden controleert. `scripts/package.py` bouwt deterministisch en verifieert de bestanden in het exacte ZIP-bestand.

## TH-01 t/m TH-16 (versie 1.0.3)

| ID | Status | Onderbouwing |
|---|---|---|
| TH-01 | PASS (source) | Blokthema en verplichte bestanden statisch geverifieerd; targetactivering ontbreekt. |
| TH-02 | PASS (source) | `theme.json` v3, geldige JSON en eenvoudige tokens; WordPress editor-roundtrip niet uitgevoerd. |
| TH-03 | PASS (source) | Bestanden, referenties en contextroutes aanwezig; echte site niet geverifieerd. |
| TH-04 | PASS (source) | Alleen Core-blokken; geen eigen PHP/JS of pluginlaag. |
| TH-05 | NOT_RUN | Gutenberg opslaan, herladen en front-end vergelijken vereist WordPress. |
| TH-06 | NOT_APPLICABLE | Geen ACF, andere verplichte plugins of ACF-schema. |
| TH-07 | PASS (source) | Geen uitvoerbare PHP/JS-code, geen meta/REST-endpoints of invoerverwerking in thema. |
| TH-08 | NOT_RUN | Geen echte WordPress-browserpagina getest op verschillende schermbreedtes. |
| TH-09 | PARTIAL | Basiscontrast statisch gemeten; keyboard/zoom/screenreader niet getest. |
| TH-10 | NOT_RUN | Core navigatie/zoekblokken aanwezig; siteclicks niet getest. |
| TH-11 | PARTIAL | Geen SEO-overrides; metadatapad/SEO-plugincompatibiliteit niet geverifieerd. |
| TH-12 | NOT_RUN | Geen CWV of netwerkmeting uitgevoerd. |
| TH-13 | NOT_RUN | Plugin levert WooCommerce-templates; producten, winkelwagen/checkout en sandboxbestelling niet getest. |
| TH-14 | PASS (source) | Exacte ZIP en bytevergelijking bij packaging; SHA-256 in eindexport. |
| TH-15 | NOT_RUN | Schone activering in WordPress ontbreekt. |
| TH-16 | PARTIAL | Syntactische checks/release zijn uitvoerbaar; runtime, echte rollback en gebruikersacceptatie ontbreken. |

Een statische templatecontrole is geen bewijs voor correct gerenderde WordPress-pagina's. Gebruik voor een productievrijgave WordPress-staging met zowel laatste en opgegeven minimumcore, minimaal PHP 8.3, Gutenberg-edit/save/reload, nieuwste-berichten-homepage, statische homepage + aparte blogpagina, archieven, zoeken, single, 404, editorrollen, responsive en toetsenbord. Test WooCommerce afzonderlijk met producten, variaties, cart, checkout, account en alleen sandboxbetalingen. Controleer daarna nogmaals de exacte geïnstalleerde ZIP en de site-restore.

## Geraadpleegde primaire bronnen

- WordPress Theme Structure: https://developer.wordpress.org/themes/core-concepts/theme-structure/
- WordPress Template Hierarchy: https://developer.wordpress.org/themes/templates/template-hierarchy/
- WordPress theme.json: https://developer.wordpress.org/block-editor/reference-guides/theme-json-reference/
- WooCommerce Block Theme: https://developer.woocommerce.com/docs/theming/block-theme-development/theming-woo-blocks/
- WooCommerce Checkout: https://developer.woocommerce.com/docs/theming/block-theme-development/cart-and-checkout/

## Onafhankelijke vervolgaudit 14 oktober 2026

De technische broncontrole heeft een best-practice-afwijking aan root padding gevonden en in v1.0.1 hersteld. De aparte, actuele audit wordt met de 1.0.3-downloadbestanden geleverd. Versie 1.0.2 heeft de source- en theme-ZIP-beveiliging aangescherpt; 1.0.3 sluit daarnaast de symlink-parentroute af. De bronbewijslast is beperkt tot offline tests: echte WordPress-, WooCommerce- en WCAG-tests blijven NOT_RUN.

## Source ZIP security fix in 1.0.2

A negative local fixture demonstrated that the 1.0.1 packager silently distributed a root `.env` file in its source ZIP and a `debug.log` under the runtime theme. The 1.0.2 packager introduced explicit allowlists, refused unexpected theme files and leaf symlinks, and added regression tests. Runtime site/editor/WooCommerce tests remain NOT_RUN.

## Actuele runtimeacceptatie (te testen, geen bewijs)

Op 14 oktober 2026 meldt WordPress.org 7.1.3 als actuele stable patchversie en WooCommerce 11.2.1 (vereist WordPress >=7.0). Test **zonder** WooCommerce op WordPress 6.6 en 7.1.3 met PHP 8.3 en 8.4, en **met** WooCommerce 11.2.1 op WordPress 7.1.3 met PHP 8.3 en 8.4. Dit is een testmatrix, geen bewering dat deze configuraties al werken. WP 6.6 is alleen voor het aantonen van de gedeclareerde minimumcompatibiliteit, niet als aanbeveling voor een nieuwe live site.

De volgende punten houden productie-GO tegen: installatie/activatie van exact de ZIP, Gutenberg editor-save-reload-frontend, WooCommerce producten/cart/checkout inclusief sandboxbetaling, echte mobiele navigatie/keyboard/reflow, WCAG 2.2 AA beoordeling, gemeten CWV en een geteste rollback. WordPress.org-themapublicatie is een afzonderlijk optioneel traject waarvoor o.a. `readme.txt`, `screenshot.png` en specifieke revieweisen moeten worden toegevoegd. Houd deze uit de minimale private starter zolang die publicatie niet gepland is.

De starter is geen garantie voor alle projectspecifieke functies (reactiesysteem, formulieren, filters, vertalingen, complexe shop-extensies). Voeg die pas per site toe vanuit WordPress Core of de relevante officieel ondersteunde plugin.

Verificatiebronnen: https://wordpress.org/documentation/wordpress-version/version-7-1-3/ ; https://wordpress.org/plugins/woocommerce/ ; https://developer.wordpress.org/themes/advanced-topics/testing/ ; https://developer.woocommerce.com/docs/theming/block-theme-development/theming-woo-blocks/ ; https://make.wordpress.org/themes/handbook/review/required/ .


### 1.0.3 security regression — ancestor symlink (verified)

Reproduction on 1.0.2: replace `theme/` with a symbolic link to another directory that contains `webactueel-starter/`. The packager exits successfully (undesired) despite its strict interior symlink policy. In 1.0.3, every component of the runtime theme path below the source root is checked and the same scenario is rejected. `test_packager_rejects_symlinked_theme_ancestor` covers this failure. The runtime theme files, apart from the version metadata, remain unchanged.

**Production QA status:** TH-05, TH-08, TH-09, TH-10, TH-12, TH-13, TH-15 and TH-16 still require independent WordPress/browser/staging evidence; do not claim a production GO or WCAG AA based on static passes.

### Aanvullende regressie-/ZIP-verificatie

Versie 1.0.3 bevat 22 Python-tests, inclusief een onafhankelijke bytevergelijking van beide gegenereerde ZIP-bestanden met de brontree en een tweede reproduceerbare build. De WordPress-thema-auditor en de externe `audit_wordpress_theme_zip.py` worden daarnaast los van de packager uitgevoerd; uitkomst en hashes staan in het meegeleverde externe auditrapport. Dit zijn **bron- en pakketcontroles**, geen vervanging voor een echte installatie.

## Repository CI follow-up (14 October 2026)

Automatic jobs run baseline source/package tests and disposable WordPress 6.6/current/WooCommerce frontend smoke tests. They do not prove full editor save/reload, WCAG 2.2 AA, CWV real-user results, shop orders/payment or production rollback. Staging release remains blocked pending corresponding TH-05, TH-09, TH-12, TH-13, TH-15 and TH-16 evidence.
