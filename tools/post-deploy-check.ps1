<#
.SYNOPSIS
Checks deployed sitemap pages and required ST8 public resources. No modules required.
.EXAMPLE
.\tools\post-deploy-check.ps1
.EXAMPLE
.\tools\post-deploy-check.ps1 -BaseUrl http://127.0.0.1:8765
#>
[CmdletBinding()]
param(
    [string]$BaseUrl = 'https://st8-ai.ru',
    [ValidateRange(1, 300)][int]$TimeoutSeconds = 20
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$rows = New-Object 'System.Collections.Generic.List[object]'
$cache = @{}

function Add-Result {
    param([string]$Check, [string]$Url, [bool]$Passed, [string]$Details)
    $status = if ($Passed) { 'OK' } else { 'FAIL' }
    $rows.Add([pscustomobject]@{ Status = $status; Check = $Check; URL = $Url; Details = $Details })
}

function Get-AttributeValue {
    param([string]$Tag, [string]$Name)
    $pattern = '(?is)(?:^|\s)' + [regex]::Escape($Name) + '\s*=\s*(?:"(?<v>[^"]*)"|''(?<v>[^'']*)''|(?<v>[^\s"''=<>`]+))'
    $match = [regex]::Match($Tag, $pattern)
    if ($match.Success) { return [System.Net.WebUtility]::HtmlDecode($match.Groups['v'].Value) }
    return ''
}

function Get-SiteUrl {
    param([string]$Path)
    return $script:siteRoot + $Path.TrimStart('/')
}

function Get-Resource {
    param([string]$Url)
    if ($cache.ContainsKey($Url)) { return $cache[$Url] }
    $response = $null
    try {
        $response = $script:client.GetAsync($Url).GetAwaiter().GetResult()
        $content = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        $result = [pscustomobject]@{ Status = [int]$response.StatusCode; Content = $content; Error = '' }
    }
    catch {
        $result = [pscustomobject]@{ Status = 0; Content = ''; Error = $_.Exception.Message }
    }
    finally { if ($null -ne $response) { $response.Dispose() } }
    $cache[$Url] = $result
    return $result
}

function Test-HtmlPage {
    param([string]$Path, [string]$Check, [string]$ExpectedCanonicalPath)
    $url = Get-SiteUrl $Path
    $resource = Get-Resource $url
    if ($resource.Status -ne 200) {
        Add-Result $Check $url $false ("HTTP {0} {1}" -f $resource.Status, $resource.Error)
        return
    }
    $problems = New-Object 'System.Collections.Generic.List[string]'
    # Ignore comments and raw text elements when counting actual HTML headings.
    $withoutComments = [regex]::Replace($resource.Content, '(?s)<!--.*?-->', '')
    $markup = [regex]::Replace($withoutComments, '(?is)<(script|style|noscript)\b[^>]*>.*?</\1\s*>', '')
    $titles = [regex]::Matches($markup, '(?is)<title\b[^>]*>(.*?)</title\s*>')
    if ($titles.Count -ne 1 -or [string]::IsNullOrWhiteSpace([regex]::Replace($titles[0].Groups[1].Value, '<[^>]*>', ''))) {
        $problems.Add('missing, empty or duplicate title')
    }
    $headings = [regex]::Matches($markup, '(?is)<h1(?=\s|>)[^>]*>')
    $headingEnds = [regex]::Matches($markup, '(?is)</h1\s*>')
    if ($headings.Count -ne 1 -or $headingEnds.Count -ne 1) { $problems.Add("h1 count $($headings.Count), closing tags $($headingEnds.Count)") }
    $canonicals = @(
        foreach ($link in [regex]::Matches($markup, '(?is)<link\b[^>]*>')) {
            $rel = Get-AttributeValue $link.Value 'rel'
            if (($rel -split '\s+') -contains 'canonical') { Get-AttributeValue $link.Value 'href' }
        }
    )
    if ($canonicals.Count -ne 1 -or [string]::IsNullOrWhiteSpace($canonicals[0])) {
        $problems.Add('missing, empty or duplicate canonical')
    }
    else {
        $canonical = $null
        if (-not [uri]::TryCreate($canonicals[0], [UriKind]::Absolute, [ref]$canonical) -or $canonical.Scheme -notin @('http', 'https')) {
            $problems.Add('canonical is not an absolute HTTP(S) URL')
        }
        elseif ($canonical.AbsolutePath -cne $ExpectedCanonicalPath) { $problems.Add('canonical path does not match requested page') }
    }
    $scripts = ([regex]::Matches($withoutComments, '(?is)<script\b[^>]*>.*?</script\s*>') | ForEach-Object { $_.Value }) -join "`n"
    if ($scripts -notmatch [regex]::Escape('G-8FVRCB166N')) { $problems.Add('GA4 code missing') }
    if ($scripts -notmatch '\b112836376\b') { $problems.Add('Metrika code missing') }
    $details = if ($problems.Count) { $problems -join '; ' } else { 'HTTP 200; title; canonical; one h1; GA4; Metrika' }
    Add-Result $Check $url ($problems.Count -eq 0) $details
}

$client = $null
$handler = $null
try {
    $baseUri = $null
    if (-not [uri]::TryCreate($BaseUrl, [UriKind]::Absolute, [ref]$baseUri) -or $baseUri.Scheme -notin @('http', 'https') -or $baseUri.Query -or $baseUri.Fragment -or $baseUri.UserInfo) {
        throw 'BaseUrl must be an absolute HTTP(S) URL without credentials, query or fragment.'
    }
    $script:siteRoot = $baseUri.AbsoluteUri.TrimEnd('/') + '/'
    Add-Type -AssemblyName System.Net.Http
    # Keep redirects visible: a 301/302 is not an HTTP 200 for the requested URL.
    $handler = New-Object System.Net.Http.HttpClientHandler
    $handler.AllowAutoRedirect = $false
    $script:client = New-Object System.Net.Http.HttpClient($handler)
    $script:client.Timeout = [TimeSpan]::FromSeconds($TimeoutSeconds)
    $script:client.DefaultRequestHeaders.UserAgent.ParseAdd('ST8-PostDeployCheck/1.0')

    $sitemapUrl = Get-SiteUrl '/sitemap.xml'
    $sitemap = Get-Resource $sitemapUrl
    $locations = @()
    if ($sitemap.Status -ne 200) {
        Add-Result 'sitemap' $sitemapUrl $false ("HTTP {0} {1}" -f $sitemap.Status, $sitemap.Error)
    }
    else {
        $reader = $null
        $textReader = $null
        try {
            $settings = New-Object System.Xml.XmlReaderSettings
            $settings.DtdProcessing = [System.Xml.DtdProcessing]::Prohibit
            $settings.XmlResolver = $null
            $textReader = New-Object System.IO.StringReader($sitemap.Content)
            $reader = [System.Xml.XmlReader]::Create($textReader, $settings)
            $document = New-Object System.Xml.XmlDocument
            $document.XmlResolver = $null
            $document.Load($reader)
            if ($document.DocumentElement.LocalName -ne 'urlset' -or $document.DocumentElement.NamespaceURI -ne 'http://www.sitemaps.org/schemas/sitemap/0.9') { throw 'Expected a sitemap urlset with the standard namespace.' }
            $locations = @($document.SelectNodes('/*[local-name()="urlset"]/*[local-name()="url"]/*[local-name()="loc"]') | ForEach-Object { $_.InnerText.Trim() })
            if ($locations.Count -eq 0) { throw 'Sitemap has no page URLs.' }
            if (@($locations | Select-Object -Unique).Count -ne $locations.Count) { throw 'Sitemap contains duplicate URLs.' }
            Add-Result 'sitemap' $sitemapUrl $true ("HTTP 200; valid XML; {0} URLs" -f $locations.Count)
        }
        catch { Add-Result 'sitemap' $sitemapUrl $false $_.Exception.Message }
        finally {
            if ($null -ne $reader) { $reader.Dispose() }
            if ($null -ne $textReader) { $textReader.Dispose() }
        }
    }

    foreach ($path in @('/robots.txt', '/llms.txt')) {
        $url = Get-SiteUrl $path
        $resource = Get-Resource $url
        $passed = $resource.Status -eq 200 -and -not [string]::IsNullOrWhiteSpace($resource.Content)
        $detail = if ($passed) { 'HTTP 200; nonempty content' } else { "HTTP $($resource.Status); missing or empty resource $($resource.Error)" }
        if ($path -eq '/robots.txt' -and $passed) {
            $directives = [regex]::Matches($resource.Content, '(?im)^\s*Sitemap\s*:\s*(\S+)')
            $hasSitemap = $false
            foreach ($directive in $directives) {
                $declared = $null
                if ([uri]::TryCreate($directive.Groups[1].Value, [UriKind]::Absolute, [ref]$declared) -and $declared.AbsolutePath -eq '/sitemap.xml') { $hasSitemap = $true }
            }
            if (-not $hasSitemap) { $passed = $false; $detail = 'robots.txt has no absolute Sitemap directive for /sitemap.xml' }
        }
        Add-Result 'resource' $url $passed $detail
    }

    foreach ($location in $locations) {
        $pageUri = $null
        if (-not [uri]::TryCreate($location, [UriKind]::Absolute, [ref]$pageUri) -or $pageUri.Scheme -notin @('http', 'https') -or $pageUri.Fragment -or $pageUri.UserInfo) {
            Add-Result 'sitemap page' $location $false 'Invalid absolute page URL'
            continue
        }
        # Use the supplied host for staging checks, while preserving sitemap paths.
        Test-HtmlPage $pageUri.PathAndQuery 'sitemap page' $pageUri.AbsolutePath
    }
    foreach ($path in @('/ae/', '/tr/', '/en/')) { Test-HtmlPage $path 'required page' $path }
}
catch { Add-Result 'checker' $BaseUrl $false $_.Exception.Message }
finally {
    if ($null -ne $client) { $client.Dispose() }
    if ($null -ne $handler) { $handler.Dispose() }
}

$rows | Format-Table Status, Check, URL, Details -AutoSize -Wrap | Out-Host
$failed = @($rows | Where-Object { $_.Status -eq 'FAIL' }).Count
Write-Host ("Checks: {0}; OK: {1}; FAIL: {2}" -f $rows.Count, ($rows.Count - $failed), $failed)
if ($failed -gt 0) { exit 1 }
exit 0
