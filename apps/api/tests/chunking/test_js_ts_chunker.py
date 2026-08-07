from lumora_api.infrastructure.chunking.js_ts_chunker import JsTsChunker

TS_SOURCE = """export interface Greeter {
  greet(name: string): string;
}

export class EnglishGreeter implements Greeter {
  greet(name: string): string {
    return `Hello, ${name}`;
  }
}

export function standaloneFunction(a: number, b: number): number {
  return a + b;
}

export const arrowFunction = (x: number): number => x * 2;
"""

JS_SOURCE = """class Animal {
  speak() {
    return "noise";
  }
}

function standalone(a, b) {
  return a + b;
}

const arrow = (x) => x * 2;
"""


def test_ts_chunker_finds_interface_class_method_function_and_arrow():
    spans = JsTsChunker("typescript").chunk(TS_SOURCE)
    by_symbol = {s.symbol: s for s in spans}

    assert by_symbol["Greeter"].kind == "interface"
    assert by_symbol["EnglishGreeter"].kind == "class"
    assert by_symbol["greet"].kind == "method"
    assert by_symbol["standaloneFunction"].kind == "function"
    assert by_symbol["arrowFunction"].kind == "function"


def test_ts_chunker_export_keyword_is_included_in_chunk_content():
    spans = JsTsChunker("typescript").chunk(TS_SOURCE)
    function_chunk = next(s for s in spans if s.symbol == "standaloneFunction")
    assert function_chunk.content.startswith("export function")


def test_js_chunker_handles_class_function_and_arrow_without_types():
    spans = JsTsChunker("javascript").chunk(JS_SOURCE)
    by_symbol = {s.symbol: s for s in spans}

    assert by_symbol["Animal"].kind == "class"
    assert by_symbol["speak"].kind == "method"
    assert by_symbol["standalone"].kind == "function"
    assert by_symbol["arrow"].kind == "function"


def test_tsx_chunker_parses_jsx_syntax():
    tsx_source = (
        "export function Greeting({ name }: { name: string }) {\n"
        "  return <div>Hello {name}</div>;\n"
        "}\n"
    )
    spans = JsTsChunker("tsx").chunk(tsx_source)
    assert any(s.symbol == "Greeting" and s.kind == "function" for s in spans)
