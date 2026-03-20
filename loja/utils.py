def formatar_iene(valor):
    if valor is None:
        return'¥0'
    return f'¥{valor:,.0f}'