from internal_gateway import model_gateway

def answer(prompt):
    return model_gateway.complete(prompt)
