// Package assets is the handplace's pages, scripts, styles and font, built into daftard so a machine needs nothing
// beside the binary and its gardens.
package assets

import "embed"

//go:embed *.html *.css *.js widgets/*.js widgets/*.css widgets/*.woff2 widgets/*.txt toolbox/*.js app/*.html app/*.js app/*.css app/pages/*.js app/pages/board/*.js served/*.html served/*.js served/*.css odoo/*.js
var FS embed.FS
