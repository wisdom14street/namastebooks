# namastebooks.com
Spiritual, metaphysical and philosophy bookstore for Namaste Bookshop (Wealth Edge Ventures Inc.). Static site on GitHub Pages, rebuilt daily from the namastebookshop.com public catalog by `.github/workflows/deploy.yml`. Checkout uses Shopify cart permalinks on namastebookshop.com with `attributes[Storefront]=Namaste Books`.
- `site/sitecopy.py`, `site/bookcls.py`: shelves, book detection and all copy. `site/p2site.py`: visit/pickup copy. `site/theme.css`: look.
- Build locally: `python3 scripts/fetch.py && python3 scripts/build.py --preview`
