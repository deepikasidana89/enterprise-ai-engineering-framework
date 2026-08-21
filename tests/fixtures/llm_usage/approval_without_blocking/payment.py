def execute_payment(request):
    if request.risk == "HIGH":
        require_human_approval(request)
    return process_payment(request)
