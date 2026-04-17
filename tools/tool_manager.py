from langchain_core.tools import tool
import ast
import math

@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression safely."""
    try:
        node = ast.parse(expression, mode='eval')

        # Whitelist allowed functions and names
        allowed_names = {'math': math, 'pi': math.pi, 'e': math.e}
        allowed_functions = {'sqrt': math.sqrt, 'pow': math.pow, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan, 'exp': math.exp, 'log': math.log}

        # Override the default visitor
        class SafeEval(ast.NodeTransformer):
            def visit_Name(self, node):
                if node.id in allowed_names:
                    return node
                else:
                    raise NameError(f"Name '{node.id}' is not allowed")

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id in allowed_functions:
                    return node
                else:
                    raise NameError(f"Function '{node.func.id if isinstance(node.func, ast.Name) else type(node.func)}' is not allowed")

            def visit_Attribute(self, node):
                if isinstance(node.value, ast.Name) and node.value.id == 'math' and node.attr in allowed_functions:
                    return node
                else:
                    raise NameError(f"Attribute '{node.attr}' is not allowed")

        # Transform the AST to only allow safe operations
        safe_eval = SafeEval()
        safe_eval.visit(node)
        ast.fix_missing_locations(node)

        code = compile(node, '<string>', 'eval')
        result = eval(code, {'__builtins__': {}}, allowed_names)  # Pass allowed names

        return str(result)
    except Exception as e:
        return f"Error: {e}"

@tool
def get_calendly_availability(query: str) -> str:
    """Check Calendly for available time slots based on the query."""
    # Placeholder for Calendly API integration.  In a real application,
    # this would use the Calendly API to find available slots.
    # For now, it returns a canned response.
    return "No specific availability information found. Please try a different query or time."

def get_tools():
    return [calculate, get_calendly_availability]