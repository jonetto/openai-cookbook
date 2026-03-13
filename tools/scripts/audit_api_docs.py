#!/usr/bin/env python3
"""
Colppy API Documentation Audit — Phase A (Tiers 1+2)

Extracts parameters from backend PHP delegates, compares against
Docusaurus markdown docs and OpenAPI YAML spec, outputs a gap report.

Usage:
    python tools/scripts/audit_api_docs.py

Output:
    tools/scripts/audit_api_docs_report.md
"""

import re
import os
import sys
from pathlib import Path
from collections import defaultdict

# ── Paths ──────────────────────────────────────────────────────────────
PROVISIONES_DIR = Path(os.path.expanduser(
    "~/openai-cookbook/github-jonetto/nubox-spa/colppy-app/resources/Provisiones"
))
DOCS_DIR = Path(os.path.expanduser("~/api-documentation/docs"))
OPENAPI_PATH = Path(os.path.expanduser(
    "~/api-documentation/static/openapi/colppy-api.yaml"
))
REPORT_PATH = Path(os.path.expanduser(
    "~/openai-cookbook/tools/scripts/audit_api_docs_report.md"
))

# Internal provisions to skip in priority rankings (still scanned)
INTERNAL_PROVISIONS = {
    "Desarrollador", "Paybook", "Referido", "Receipt", "Help",
    "Notificaciones", "Socio", "BillStub", "Importer", "Integracion",
    "Tercero", "Pos", "ColppyCommon"
}

# Internal methods that aren't API operations
INTERNAL_METHODS = {"__http_bypass", "__http_blacklist", "__http_list", "__construct"}

# Meta-params that come from the framework, not the user
FRAMEWORK_PARAMS = {
    "sesion", "oauth", "idUsuario", "idTabla", "nueva", "country_id",
    "nroFactura", "descripcion"
}


# ── 1. Extract operations + params from backend ───────────────────────

def _split_php_functions(content: str) -> dict:
    """
    Split PHP file content into {function_name: function_body} by finding
    function declarations and using brace counting for boundaries.
    """
    functions = {}
    # Find all function declarations
    pattern = re.compile(
        r'(?:public|private|protected)\s+function\s+(\w+)\s*\([^)]*\)\s*\{',
        re.DOTALL,
    )
    matches = list(pattern.finditer(content))
    for idx, match in enumerate(matches):
        func_name = match.group(1)
        start = match.end()  # after the opening {
        # Find the matching closing brace using brace counting
        depth = 1
        pos = start
        while pos < len(content) and depth > 0:
            ch = content[pos]
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
            pos += 1
        functions[func_name] = content[start:pos - 1] if depth == 0 else content[start:]
    return functions


def _extract_params_from_body(body: str) -> tuple:
    """Extract (flat_params, isset_params, nested_params) from a function body."""
    flat = set()
    isset = set()
    nested = set()

    for m in re.finditer(r'\$parametros->(\w+)', body):
        p = m.group(1)
        if p not in FRAMEWORK_PARAMS:
            flat.add(p)

    for m in re.finditer(r'isset\s*\(\s*\$parametros->(\w+)', body):
        isset.add(m.group(1))

    for m in re.finditer(r'\$parametros->(\w+)->(\w+)', body):
        nested.add(f"{m.group(1)}.{m.group(2)}")

    return flat, isset, nested


def extract_operations(provisiones_dir: Path) -> dict:
    """
    Per-operation param extraction using function-level PHP parsing.

    Strategy:
    1. Read main Provision.php → extract operation names
    2. For each operation, trace which delegate class + method it calls
    3. In that delegate, parse just that function's body for $parametros->
    4. Also scan FacturaCommon.php for shared operations (alta/editar)

    Returns: {
        "ProvisionName": {
            "operation_name": {
                "params": {"paramName", ...},
                "nested_params": {"info_general.fieldName", ...},
                "isset_checks": {"optionalParam", ...},
                "delegate_file": "path/to/Delegate.php"
            }
        }
    }
    """
    # Pre-scan FacturaCommon for shared params
    factura_common_path = (
        provisiones_dir / "ColppyCommon" / "common" / "FacturaCommon.php"
    )
    factura_common_funcs = {}
    if factura_common_path.exists():
        fc_content = factura_common_path.read_text(errors="replace")
        factura_common_funcs = _split_php_functions(fc_content)

    result = {}
    for prov_dir in sorted(provisiones_dir.iterdir()):
        if not prov_dir.is_dir() or prov_dir.name == "ColppyCommon":
            continue
        prov_name = prov_dir.name
        main_php = prov_dir / "1_0_0_0" / f"{prov_name}.php"
        if not main_php.exists():
            continue

        main_content = main_php.read_text(errors="replace")
        operations = {}

        # Extract operation names + find which delegate method they call
        for match in re.finditer(
            r'public\s+function\s+(\w+)\s*\(', main_content
        ):
            op_name = match.group(1)
            if op_name in INTERNAL_METHODS:
                continue
            operations[op_name] = {
                "params": set(),
                "nested_params": set(),
                "isset_checks": set(),
                "delegate_file": str(main_php),
            }

        # Build a lookup of all functions across all delegate files
        delegates_dir = prov_dir / "1_0_0_0" / "delegates"
        all_delegate_funcs = {}  # {func_name: (body, file_path)}

        if delegates_dir.exists():
            for php_file in sorted(delegates_dir.glob("*.php")):
                if php_file.name == "AbstractDelegate.php":
                    continue
                content = php_file.read_text(errors="replace")
                funcs = _split_php_functions(content)
                for fname, fbody in funcs.items():
                    all_delegate_funcs[fname] = (fbody, str(php_file))

        # Map each operation to its delegate function
        for op_name, op_data in operations.items():
            # Try exact match first, then case-insensitive
            func_body = None
            func_file = None

            if op_name in all_delegate_funcs:
                func_body, func_file = all_delegate_funcs[op_name]
            else:
                # Case-insensitive fallback
                for fname, (fbody, fpath) in all_delegate_funcs.items():
                    if fname.lower() == op_name.lower():
                        func_body, func_file = fbody, fpath
                        break

            if func_body:
                op_data["delegate_file"] = func_file
                flat, isset, nested = _extract_params_from_body(func_body)
                op_data["params"] = flat
                op_data["isset_checks"] = isset
                op_data["nested_params"] = nested

                # If this function calls a FacturaCommon method, merge those params
                for common_call in re.finditer(
                    r'(?:FacturaCommon|Common)\w*::\s*(\w+)|'
                    r'\$(?:common|facturaCommon)\w*->\s*(\w+)',
                    func_body,
                ):
                    called = common_call.group(1) or common_call.group(2)
                    if called in factura_common_funcs:
                        cf, ci, cn = _extract_params_from_body(
                            factura_common_funcs[called]
                        )
                        op_data["params"] |= cf
                        op_data["isset_checks"] |= ci
                        op_data["nested_params"] |= cn

        result[prov_name] = operations
    return result


# ── 2. Extract documented operations + params from Docusaurus .md ─────

def extract_docs(docs_dir: Path) -> dict:
    """
    Returns: {
        "ProvisionName": {
            "operation_name": {
                "params": set(),
                "has_request_example": bool,
                "has_response_example": bool,
            }
        }
    }
    """
    result = {}
    for md_file in sorted(docs_dir.rglob("*.md")):
        if md_file.name in ("faq.md", "intro.md"):
            continue
        content = md_file.read_text(errors="replace")

        # Determine provision name from the H1 heading
        h1_match = re.search(r'^#\s+(\w+)', content, re.MULTILINE)
        if not h1_match:
            continue
        prov_name = h1_match.group(1)

        operations = {}
        # Find H2 sections that look like operation names
        sections = re.split(r'^##\s+', content, flags=re.MULTILINE)
        for section in sections[1:]:  # skip before first H2
            lines = section.strip().split('\n')
            op_name = lines[0].strip()
            # Skip non-operation sections
            if op_name in (
                "Operaciones Disponibles", "Tipos de Comprobantes",
                "Estados de Factura", "Validaciones de Fecha",
                "Condiciones de Pago", "Notas"
            ):
                continue
            # Skip if it doesn't look like an operation name
            if ' ' in op_name and not op_name.startswith(('alta_', 'editar_', 'leer_', 'listar_', 'borrar_')):
                continue

            section_text = '\n'.join(lines[1:])
            params = set()

            # Extract params from tables: | `paramName` | type | ...
            for m in re.finditer(r'\|\s*`(\w+)`\s*\|', section_text):
                params.add(m.group(1))

            # Also extract params from JSON code blocks
            for m in re.finditer(r'"(\w+)"(?:\s*:)', section_text):
                p = m.group(1)
                if p not in (
                    "auth", "service", "provision", "operacion",
                    "usuario", "password", "sesion", "success", "message",
                    "data", "detalle", "infofactura", "itemsFactura",
                    "total", "property", "value"
                ):
                    params.add(p)

            operations[op_name] = {
                "params": params,
                "has_request_example": "```json" in section_text
                    and '"service"' in section_text,
                "has_response_example": '"success"' in section_text,
                "source_file": str(md_file),
            }

        if operations:
            result[prov_name] = operations
    return result


# ── 3. Extract from OpenAPI YAML ──────────────────────────────────────

def extract_openapi(yaml_path: Path) -> dict:
    """
    Simple YAML parser (no dependency on pyyaml) — extracts operation paths
    and schema property names.

    Returns: {
        "ProvisionName": {
            "operation_name": {
                "params": set(),
                "has_schema": bool,
            }
        }
    }
    """
    if not yaml_path.exists():
        return {}

    content = yaml_path.read_text(errors="replace")
    result = {}

    # Extract paths like /Proveedor/alta_proveedor
    for match in re.finditer(
        r'^\s+/(\w+)/(\w+):', content, re.MULTILINE
    ):
        prov = match.group(1)
        op = match.group(2)
        if prov not in result:
            result[prov] = {}
        result[prov][op] = {"params": set(), "has_schema": False}

    # Extract schema definitions and their properties
    # Look for patterns like:
    #   AltaProveedorRequest:
    #     ...
    #     properties:
    #       paramName:
    current_schema = None
    in_properties = False
    indent_level = 0

    for line in content.split('\n'):
        # Detect schema definition
        schema_match = re.match(r'^    (\w+Request):', line)
        if schema_match:
            current_schema = schema_match.group(1)
            in_properties = False
            continue

        if current_schema:
            if re.match(r'^      properties:', line):
                in_properties = True
                continue
            if in_properties:
                # Property at 8-space indent
                prop_match = re.match(r'^        (\w+):', line)
                if prop_match:
                    prop_name = prop_match.group(1)
                    # Map schema name back to provision/operation
                    # e.g., AltaProveedorRequest → Proveedor/alta_proveedor
                    for prov, ops in result.items():
                        for op, data in ops.items():
                            schema_prefix = op.replace('_', '').lower()
                            if current_schema.lower().startswith(
                                schema_prefix.replace(prov.lower(), '')
                            ) or prov.lower() in current_schema.lower():
                                data["params"].add(prop_name)
                                data["has_schema"] = True
                elif not line.startswith('          ') and line.strip() and not line.startswith('        '):
                    in_properties = False

    return result


# ── 4. Build the gap report ───────────────────────────────────────────

def build_report(backend, docs, openapi) -> str:
    lines = []
    lines.append("# Colppy API Documentation Audit Report")
    lines.append(f"\nGenerated: {__import__('datetime').date.today()}")
    lines.append("")

    # ── Summary stats ──
    total_provisions = len(backend)
    total_ops = sum(len(ops) for ops in backend.values())
    doc_provisions = len(docs)
    doc_ops = sum(len(ops) for ops in docs.values())
    api_provisions = len(openapi)
    api_ops = sum(len(ops) for ops in openapi.values())

    lines.append("## Coverage Summary\n")
    lines.append("| | Backend | Docusaurus | OpenAPI |")
    lines.append("|--|---------|------------|---------|")
    lines.append(
        f"| Provisions | **{total_provisions}** | "
        f"{doc_provisions} ({doc_provisions*100//total_provisions}%) | "
        f"{api_provisions} ({api_provisions*100//max(total_provisions,1)}%) |"
    )
    lines.append(
        f"| Operations | **{total_ops}** | "
        f"{doc_ops} ({doc_ops*100//max(total_ops,1)}%) | "
        f"{api_ops} ({api_ops*100//max(total_ops,1)}%) |"
    )

    # ── Undocumented provisions ──
    lines.append("\n## Undocumented Provisions\n")
    lines.append(
        "Provisions that exist in backend but have NO Docusaurus documentation.\n"
    )
    undoc_provs = sorted(
        set(backend.keys()) - set(docs.keys()) - INTERNAL_PROVISIONS
    )
    internal_provs = sorted(
        set(backend.keys()) - set(docs.keys()) & INTERNAL_PROVISIONS
    )

    if undoc_provs:
        lines.append("### Should Document (user-facing)\n")
        lines.append("| Provision | Operations | Key Operations |")
        lines.append("|-----------|-----------|----------------|")
        for prov in undoc_provs:
            ops = backend[prov]
            op_names = sorted(ops.keys())
            # Show first 5 interesting operations
            interesting = [
                o for o in op_names
                if any(o.startswith(p) for p in (
                    "alta_", "editar_", "leer_", "listar_", "borrar_"
                ))
            ][:5]
            lines.append(
                f"| **{prov}** | {len(ops)} | "
                f"`{'`, `'.join(interesting) if interesting else 'N/A'}` |"
            )

    lines.append("\n### Internal/Skip\n")
    skip_provs = sorted(
        (set(backend.keys()) - set(docs.keys())) & INTERNAL_PROVISIONS
    )
    if skip_provs:
        lines.append(
            ", ".join(f"`{p}`" for p in skip_provs)
        )

    # ── Per-provision detailed analysis ──
    lines.append("\n---\n")
    lines.append("## Per-Provision Analysis\n")

    for prov_name in sorted(backend.keys()):
        if prov_name in INTERNAL_PROVISIONS:
            continue

        backend_ops = backend[prov_name]
        doc_ops_dict = docs.get(prov_name, {})
        api_ops_dict = openapi.get(prov_name, {})

        lines.append(f"\n### {prov_name}\n")

        # Operation coverage table
        lines.append("| Operation | Backend | Docs | OpenAPI | Missing Params (in backend, not in docs) |")
        lines.append("|-----------|:-------:|:----:|:-------:|----------------------------------------|")

        for op_name in sorted(backend_ops.keys()):
            in_docs = "✅" if op_name in doc_ops_dict else "❌"
            in_api = "✅" if op_name in api_ops_dict else "❌"

            # Param diff: what's in backend but not in docs
            backend_params = backend_ops[op_name].get("params", set())
            doc_params = doc_ops_dict.get(op_name, {}).get("params", set())
            # Remove framework params for comparison
            backend_user_params = backend_params - FRAMEWORK_PARAMS
            missing_in_docs = sorted(backend_user_params - doc_params)

            missing_str = ""
            if op_name in doc_ops_dict and missing_in_docs:
                # Show max 8 missing params
                shown = missing_in_docs[:8]
                extra = len(missing_in_docs) - 8
                missing_str = ", ".join(f"`{p}`" for p in shown)
                if extra > 0:
                    missing_str += f" +{extra} more"
            elif op_name not in doc_ops_dict:
                missing_str = "*(entire operation undocumented)*"

            lines.append(
                f"| `{op_name}` | ✅ | {in_docs} | {in_api} | {missing_str} |"
            )

        # Extra operations in docs but NOT in backend (potential stale docs)
        doc_only = set(doc_ops_dict.keys()) - set(backend_ops.keys())
        if doc_only:
            lines.append(f"\n⚠️ **In docs but NOT in backend:** {', '.join(f'`{o}`' for o in sorted(doc_only))}")

    # ── OpenAPI gap summary ──
    lines.append("\n---\n")
    lines.append("## OpenAPI Coverage Gap\n")
    lines.append(
        "Operations documented in Docusaurus but missing from OpenAPI YAML:\n"
    )
    lines.append("| Provision | Operation | In Docs | In OpenAPI |")
    lines.append("|-----------|-----------|:-------:|:----------:|")

    for prov in sorted(docs.keys()):
        for op in sorted(docs[prov].keys()):
            in_api = op in openapi.get(prov, {})
            if not in_api:
                lines.append(f"| {prov} | `{op}` | ✅ | ❌ |")

    # ── Priority recommendations ──
    lines.append("\n---\n")
    lines.append("## Recommended Actions\n")
    lines.append("### High Priority (user-facing, undocumented operations)\n")

    high_priority = []
    for prov in sorted(backend.keys()):
        if prov in INTERNAL_PROVISIONS:
            continue
        if prov in docs:
            undoc_ops = set(backend[prov].keys()) - set(docs[prov].keys())
            # Filter to CRUD-like operations
            crud_ops = [
                o for o in undoc_ops
                if any(o.startswith(p) for p in (
                    "alta_", "editar_", "leer_", "listar_", "borrar_"
                ))
            ]
            if crud_ops:
                high_priority.append((prov, sorted(crud_ops)))

    for prov, ops in high_priority:
        lines.append(f"- **{prov}**: {', '.join(f'`{o}`' for o in ops)}")

    lines.append("\n### Medium Priority (OpenAPI sync needed)\n")
    lines.append(
        "Sync Docusaurus-documented operations into the OpenAPI YAML spec "
        "for AI/MCP consumption.\n"
    )

    openapi_gap_count = 0
    for prov in docs:
        for op in docs[prov]:
            if op not in openapi.get(prov, {}):
                openapi_gap_count += 1
    lines.append(
        f"**{openapi_gap_count} operations** documented in Markdown but "
        f"missing from OpenAPI."
    )

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────

def main():
    print("🔍 Phase A: Colppy API Documentation Audit")
    print(f"   Backend:  {PROVISIONES_DIR}")
    print(f"   Docs:     {DOCS_DIR}")
    print(f"   OpenAPI:  {OPENAPI_PATH}")
    print()

    # Step 1: Extract from backend
    print("1/4 Extracting operations from backend PHP...")
    backend = extract_operations(PROVISIONES_DIR)
    total_ops = sum(len(ops) for ops in backend.values())
    print(f"     Found {len(backend)} provisions, {total_ops} operations")

    # Step 2: Extract from docs
    print("2/4 Parsing Docusaurus markdown files...")
    docs = extract_docs(DOCS_DIR)
    doc_ops = sum(len(ops) for ops in docs.values())
    print(f"     Found {len(docs)} documented provisions, {doc_ops} operations")

    # Step 3: Extract from OpenAPI
    print("3/4 Parsing OpenAPI YAML spec...")
    openapi = extract_openapi(OPENAPI_PATH)
    api_ops = sum(len(ops) for ops in openapi.values())
    print(f"     Found {len(openapi)} provisions, {api_ops} operations in OpenAPI")

    # Step 4: Generate report
    print("4/4 Generating gap report...")
    report = build_report(backend, docs, openapi)
    REPORT_PATH.write_text(report)
    print(f"\n✅ Report saved to: {REPORT_PATH}")
    print(f"   ({len(report)} chars, {report.count(chr(10))} lines)")


if __name__ == "__main__":
    main()
