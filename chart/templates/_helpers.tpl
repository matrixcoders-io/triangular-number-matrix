{{/*
Expand the chart name.
*/}}
{{- define "tnm.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Full release name — used as the primary resource name throughout.
Truncated to 63 chars (Kubernetes label limit).
*/}}
{{- define "tnm.fullname" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels applied to every resource.
*/}}
{{- define "tnm.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "tnm.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels — used by Service and Deployment to match pods.
Must stay stable across upgrades (never add dynamic values here).
*/}}
{{- define "tnm.selectorLabels" -}}
app.kubernetes.io/name: {{ include "tnm.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
