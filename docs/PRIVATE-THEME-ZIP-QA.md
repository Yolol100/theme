# Herbruikbare prive-thema-ZIP-test

Deze workflow in Yolol100/theme is een generieke GitHub-hosted acceptatietest. De bestaande Docker Compose-omgeving wordt hergebruikt. Er wordt niets gepubliceerd of gedeployed.

## Geautoriseerde private caller

Roep de reusable workflow vanuit een PRIVATE GitHub-repository aan. Laat een eerdere job in DEZELFDE workflow-run de exacte theme ZIP als Actions artifact uploaden en de SHA-256 berekenen. Bewaar die output in een job-output. Gebruik een onveranderlijke 40-tekens commit SHA om de harness te pinnen. Voorbeeld:

    jobs:
      qa:
        needs: build
        uses: Yolol100/theme/.github/workflows/private-theme-zip-qa.yml@FULL_PINNED_SHA
        with:
          harness_sha: FULL_PINNED_SHA
          artifact_name: private-theme-zip
          archive_name: theme.zip
          zip_sha256: BUILD_JOB_SHA256_OUTPUT
          theme_slug: private-theme

Vervang voorbeeldwaarden door werkelijk gecontroleerde waarden en gebruik de juiste build-job-expression. Build-resultaat, broncommit en ZIP-hash moeten afzonderlijk gekoppeld zijn; de harness kan uit alleen een ZIP-hash niet bewijzen welke private bronbestanden werden verpakt.

## Controles en bewijsgrenzen

ZIP: verwachte SHA-256, enkele root, geldige WordPress-structuur, CRC, pad- en symlinkbeveiliging. Runtime: geïsoleerde WordPress/MariaDB, activering, WP-CLI save/readback, HTTP, Chromium/Firefox/WebKit, 13 viewports, no-JS, eerste-partij fouten, axe, foutlog en JSON-artifact.

NIET UITGEVOERD: echte Gutenberg Site Editor UI, klantspecifieke flows, echte betalingen, Lighthouse-herhaalde runs, echte staging-back-up, WCAG-EM en screenreader. Geen productie-go.

De publieke workflow PR/selftest gebruikt uitsluitend het eigen publieke starter-thema. Private ZIPs, screenshots, credentials, logs of klantcode mogen nooit in de publieke repository of publieke artifacts. Het private workflowartifact blijft bij de private caller. Test alleen geautoriseerde, vooraf beoordeelde ZIPs: PHP-code kan actief worden uitgevoerd en deze teststraat is geen onbreekbare sandbox.

Bij een mislukking heeft de workflow status FAIL; installatie, browser en acceptatie blijven NOT_RUN indien het eerdere stadium faalt. Releasemerge en deploy volgen aparte toestemming.
