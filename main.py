import streamlit as st
import pandas as pd
import numpy_financial as npf

st.image('https://static-resource.homecapital.com.co/homecapital/logo-horizontal-homecapital.svg', width=400)
st.title('Calculadora feria tu vivienda')

proyectos = pd.read_csv('proyectos_hc.csv', sep=';')


def plan_pagos(valor, interes, periodos):
    original_balance = valor
    coupon = interes
    term = periodos
    periods = range(1, term + 1)
    interest_payment = npf.ipmt(
        rate=(1 + coupon) ** (1 / 12) - 1, per=periods, nper=term, pv=-original_balance)
    principal_payment = npf.ppmt(
        rate=coupon / 12, per=periods, nper=term, pv=-original_balance)
    cf_data = {'Interest': interest_payment, 'Principal': principal_payment}
    cf_table = pd.DataFrame(data=cf_data, index=periods)
    cf_table['Payment'] = npf.pmt((1 + coupon) ** (1 / 12) - 1, term, -original_balance)
    cf_table['Principal'] = cf_table['Payment'] - cf_table['Interest']
    cf_table['Ending Balance'] = original_balance - \
                                 cf_table['Principal'].cumsum()
    cf_table['Beginning Balance'] = [original_balance] + \
                                    list(cf_table['Ending Balance'])[:-1]
    cf_table = cf_table[['Beginning Balance', 'Payment', 'Interest',
                         'Principal', 'Ending Balance']]

    return cf_table


def flujo_caja_tir(comision_venta, costos_notariales_vent, precio_descuento, financiacion, retefuente_venta, plan_pago,
                   flujo_valorizacion, flujo_gastos, fecha_liq_inversion, valor_inicial_tir):
    periodos = fecha_liq_inversion * 12
    flujos_tir = pd.DataFrame({'periodo': [int(i) for i in range(periodos)]},
                              columns=['periodo', 'valor',
                                       'costo_venta', 'valor_venta',
                                       'saldo_deuda', 'flujo_caja_tir'])
    flujo_valorizacion.valor_subsidio.fillna(0, inplace=True)
    flujos_tir.set_index('periodo', inplace=True)
    flujos_tir.loc[0, 'valor'] = valor_inicial_tir

    A = 2022
    for i in range(1, periodos + 1):
        try:
            flujos_tir.loc[i, 'valor'] = flujo_valorizacion.loc[A, 'valor_arriendo'] - flujo_gastos.loc[A, 'total'] - \
                                     plan_pago.loc[i + 1, 'Payment'] + (
                                                 1 * (flujo_valorizacion.loc[A, 'valor_subsidio']))
        except:
            flujos_tir.loc[i, 'valor'] = flujo_valorizacion.loc[A, 'valor_arriendo'] - flujo_gastos.loc[A, 'total'] - \
                                         plan_pago.loc[i + 1, 'Payment'] + (
                                                 1 * (flujo_valorizacion.loc[A, 'valor_subsidio']))

        if (i % 12 == 0):
            A = A + 1

    if financiacion != 0:
        financiacion = 1
    else:
        financiacion = 0

    for i in range(1, periodos + 1):

        if i == periodos:
            flujos_tir.loc[i, 'costo_venta'] = (flujo_valorizacion.loc[int(2021+(i/12)),'valor_inmueble']*comision_venta) +\
                                               (flujo_valorizacion.loc[int(2021+(i/12)),'valor_inmueble']*retefuente_venta)+\
                                               (financiacion*(costos_notariales_vent*precio_descuento))

            flujos_tir.loc[i, 'valor_venta'] = flujo_valorizacion.loc[2021 +(i / 12), 'valor_inmueble']
            flujos_tir.loc[i, 'saldo_deuda'] = plan_pago.loc[i, 'Ending Balance']
            flujos_tir.loc[i, 'flujo_caja_tir'] = flujos_tir.loc[i, 'valor'] - flujos_tir.loc[i, 'costo_venta'] + \
                                                  flujos_tir.loc[i, 'valor_venta'] - flujos_tir.loc[i, 'saldo_deuda']
        else:
            flujos_tir.loc[i, 'costo_venta'] = 0
            flujos_tir.loc[i, 'valor_venta'] = 0
            flujos_tir.loc[i, 'saldo_deuda'] = 0
            flujos_tir.loc[0, 'flujo_caja_tir'] = valor_inicial_tir
            flujos_tir.loc[i, 'flujo_caja_tir'] = flujos_tir.loc[i, 'valor'] - flujos_tir.loc[i, 'costo_venta'] + \
                                                  flujos_tir.loc[i, 'valor_venta'] - flujos_tir.loc[i, 'saldo_deuda']
    flujos_tir.fillna(0, inplace=True)

    return flujos_tir


def valorizacion(valor_arriendo, valor_inmueble, liquidacion, valorizacion, peridios_sub, subsidio=0):
    flujo_valorizacion = pd.DataFrame({'año': [2022 + i for i in range(liquidacion)]},
                                      columns=['año', 'IPC', 'valorizacion',
                                               'valor_arriendo', 'valor_inmueble',
                                               'valor_subsidio'])

    flujo_valorizacion.set_index('año', inplace=True)
    flujo_valorizacion.loc[2022, 'IPC'] = 0.069
    flujo_valorizacion.loc[2023, 'IPC'] = 0.038
    flujo_valorizacion.loc[2022, 'valor_inmueble'] = valor_inmueble * (
                1 + valorizacion + flujo_valorizacion.loc[2022, 'IPC'])
    flujo_valorizacion.loc[2022, 'valor_arriendo'] = valor_arriendo

    for i in range(peridios_sub):
        flujo_valorizacion.loc[2022 + i, 'valor_subsidio'] = subsidio

    for i in range(liquidacion):
        flujo_valorizacion.loc[2024:, 'IPC'] = 0.03
    for i in range(liquidacion):
        flujo_valorizacion.loc[2022:, 'valorizacion'] = valorizacion

    for i in range(liquidacion):
        flujo_valorizacion.loc[2023 + i, 'valor_arriendo'] = flujo_valorizacion.loc[2022 + i, 'valor_arriendo'] * (
                    1 + flujo_valorizacion.loc[2022 + i, 'IPC'])

    for i in range(liquidacion):
        flujo_valorizacion.loc[2023 + i, 'valor_inmueble'] = flujo_valorizacion.loc[2022 + i, 'valor_inmueble'] * \
                                                             (1 + ((flujo_valorizacion.loc[2023 + i, 'IPC']) + (
                                                             flujo_valorizacion.loc[2023 + i, 'valorizacion'])))

    return flujo_valorizacion


def flujo_gastos(flujo_valorizacion, liquidacion, administracion, comision_arriendo, predial, valor_financiacion,
                 seguro_vida, seguro_it_atm, prov_sostenimiento, valor_inmb):
    flujo_gastos = pd.DataFrame({'año': [2022 + i for i in range(liquidacion)]})

    flujo_gastos.set_index('año', inplace=True)
    flujo_gastos.loc[2022, 'administracion'] = administracion
    flujo_gastos.loc[2022, 'comision_arriendo'] = flujo_valorizacion.loc[
                                                      2022, 'valor_arriendo'] * comision_arriendo * 1.19
    flujo_gastos.loc[2022, 'predial'] = valor_inmb * (predial / 12)
    flujo_gastos['seguro_vida'] = (valor_financiacion / 1000000) * seguro_vida
    flujo_gastos['seguro_it_atm'] = seguro_it_atm
    flujo_gastos.loc[2022, 'prov_sostenimiento'] = prov_sostenimiento * valor_inmb

    for i in range(liquidacion):
        flujo_gastos.loc[2023 + i, 'administracion'] = flujo_gastos.loc[2022 + i, 'administracion'] * (
                    1 + flujo_valorizacion.loc[2022 + i, 'IPC'])

    for i in range(liquidacion):
        flujo_gastos.loc[2023 + i, 'comision_arriendo'] = flujo_valorizacion.loc[2023 + i, 'valor_arriendo'] * (
            comision_arriendo) * 1.19

    for i in range(liquidacion):
        flujo_gastos.loc[2023 + i, 'predial'] = flujo_valorizacion.loc[2022 + i, 'valor_inmueble'] * (predial / 12)

    for i in range(liquidacion):
        flujo_gastos.loc[2023 + i, 'seguro_vida'] = (valor_financiacion / 1000000) * seguro_vida

    for i in range(liquidacion):
        flujo_gastos.loc[2023 + i, 'seguro_it_atm'] = seguro_it_atm

    for i in range(liquidacion):
        flujo_gastos.loc[2023 + i, 'prov_sostenimiento'] = flujo_valorizacion.loc[
                                                               2022 + i, 'valor_inmueble'] * prov_sostenimiento

    flujo_gastos['total'] = flujo_gastos.sum(axis=1)

    return flujo_gastos


def calcular_tir_MV(flujos):
    return npf.irr(flujos)

def calcular_tir_EA(tirMV):
    return (1+tirMV)**12-1

@st.cache
def convert_df(df):
   return df.to_csv().encode('utf-8')



def tir_7():
    tir_7 = pd.DataFrame({'año': [int(2022 + i) for i in range(7)]},
                         columns=['año', 'TIR Efectiva Anual', 'TIR Mes Vencido'])
    tir_7.set_index('año', inplace=True)
    for i in range(7):
        flujo_valorizacion = valorizacion(valor_arriendo, valor_inmueble, round(i, 0), param_valorizacion,
                                          periodos_subsidio, subsidio)
        flujo_gasto = flujo_gastos(flujo_valorizacion, round(i, 0), parametros_iniciales['administracion'].item(),
                                   parametros_iniciales['comision_arriendo'].item(),
                                   parametros_iniciales['predial'].item(),
                                   valor_financiado, parametros_iniciales['seguro_vida'].item(),
                                   parametros_iniciales['seguro_it_amit'].item(),
                                   parametros_iniciales['prov_sostenimiento'].item(), valor_inmueble)
        precalculotir = flujo_caja_tir(parametros_iniciales['comision_venta'].item(),
                                       parametros_iniciales['costo_not_venta'].item(),
                                       proyecto['Precio con descuento'].item(),
                                       porcentaje_financiado, parametros_iniciales['retefuente_venta'].item(),
                                       plan_pago,
                                       flujo_valorizacion, flujo_gasto, round(i, 0), valor_inicial_tir)
        tir_MV = calcular_tir_MV(precalculotir.loc[0:i * 12, 'flujo_caja_tir'])
        tir_EA = calcular_tir_EA(tir_MV)
        tir_7.loc[2022 + i , 'TIR Mes Vencido'] = tir_MV*100
        tir_7.loc[2022 + i, 'TIR Efectiva Anual'] = tir_EA*100

    return tir_7

select_sidebar = st.sidebar.selectbox('Parametros personalizados', ('', 'Actualizar parametros'))

parametros_iniciales = None

if select_sidebar == 'Actualizar parametros':
    file = st.sidebar.file_uploader('Archivo de parametros', type='csv')
    st.sidebar.download_button("Ejemplo formato parametros", 'parametros_iniciales.csv', "file.csv","text/csv",key='download-csv')
    if file is not None:
        parametros_iniciales = pd.read_csv(file, sep=';')
else:
    parametros_iniciales = pd.read_csv('parametros_iniciales.csv', sep=';')

opciones = proyectos['proyecto'].values.tolist()

selectbox_options = st.selectbox('Inmueble', options=opciones, key=1)

if selectbox_options != '' and parametros_iniciales is not None :
    parametros_iniciales = parametros_iniciales[parametros_iniciales['proyecto'] == selectbox_options]
    proyectos = proyectos[proyectos['proyecto'] == selectbox_options]
    st.markdown('**Descuento Home Capital**')
    proyecto = proyectos[proyectos['proyecto'] == selectbox_options]
    st.markdown('**Proyecto**: {}'.format(proyecto['proyecto'].item()))
    st.markdown('**Precio Portales**: {}'.format(proyecto['precio_portales'].item()))
    st.markdown('**Precio con descuento HC**: {}'.format(proyecto['Precio con descuento'].item()))
    if st.checkbox('Descuento adicional'):
        col1,col2 = st.columns([1,2])
        with col1:
            descuento_adicional = int(st.number_input('Porcentaje descuento adicional'))/100
        with col2:
            valor_inmueble_desc_adicional = st.number_input('Valor inmueble',proyecto['Precio con descuento'].item()*(1-descuento_adicional), disabled=True)
            proyecto['Precio con descuento'] = valor_inmueble_desc_adicional
    st.subheader('Simulación de inversión')
    container_2 = st.container()
    col1, col2 = container_2.columns(2)
    with col1:
        st.markdown('**Inversión**')
        inversion_inicial = int(st.number_input('Inversión inicial',format='%f'))
        valor_financiado = st.number_input('Valor a financiar',int(proyecto['Precio con descuento']-inversion_inicial),format='%d', disabled=True)
        valor_inmueble = proyecto['precio_portales'].item()
        porcentaje_financiado = st.text_input('Porcentaje financiado', '{:2.2%}'.format(valor_financiado/ proyecto['Precio con descuento'].item()), disabled=True)
    with col2:
        st.markdown('**Condiciones crédito**')
        plazo_credito = st.number_input('Plazo crédito en años',min_value=7,max_value=25)
        tasa_credito = st.number_input('tasa crédito Efectiva Anual',format="%.2f")/100
        plazo_credito_mes = int(st.number_input('plazo crédito meses', plazo_credito*12, disabled=True))
        tasa_credito_mes = st.number_input('tasa crédito Mes Vencido',((1+tasa_credito)**(1/12)-1)*100, format="%.2f",disabled=True)/100
        valor_inicial_tir = -inversion_inicial - ((proyecto['Precio con descuento'].item()*parametros_iniciales['registro_compra'].item())  + \
                                            (proyecto['Precio con descuento'].item())*parametros_iniciales['costo_not_venta'].item()) - parametros_iniciales['comision_compra'].item()

    if tasa_credito_mes != 0:
        container_3 = st.container()
        with container_3:
            st.markdown('**Plan Arriendo**')
            fecha_liq_inversion = st.number_input('liquidación de inversión en años',value=5, max_value=7)
            subsidio_op = st.checkbox('Aplica subsidio')
            col1, col2 = container_3.columns([10,7])
            with col1:
                if subsidio_op is True:
                    subsidio = int(st.number_input('Valor Subsidio',format='%f'))
                else:
                    subsidio = int(st.number_input('Valor Subsidio', 0, disabled=True))
            with col2:
                if subsidio_op is True:
                    periodos_subsidio = int(st.number_input('Número de periodos del subsidio en años',format='%x'))
                else:
                    periodos_subsidio = int(st.number_input('Número de periodos del subsidio', 0,format='%x', disabled=True))

            col3, col4 = container_3.columns([4,3])
            with col3:
                valor_arriendo = st.number_input('Valor estimado de arriendo', format='%f')
            with col4:
                valor_arriendo_sugerido = st.number_input('Valor arriendo sugerido', value=round(valor_inmueble*0.0045,0), format='%f', disabled=True)

        if valor_arriendo != 0:
            param_valorizacion = st.number_input('Factor de valorizacion',value=3)/100
            if param_valorizacion != 0:
                #rentabilidad_arriendo_mensual = st.text_input('Rentabilidad mensual', '{}%'.format(0.80 * 100),
                #                                                   disabled=True)
                #rentabilidad_arriendo_anual = st.text_input('Rentabilidad anual', '{}%'.format(0.80 * 100),
                #                                                 disabled=True)
                flujo_valorizacion =valorizacion(valor_arriendo,valor_inmueble,round(fecha_liq_inversion,0),param_valorizacion,periodos_subsidio,subsidio)
                flujo_gasto = flujo_gastos(flujo_valorizacion,round(fecha_liq_inversion,0),parametros_iniciales['administracion'].item(),
                                           parametros_iniciales['comision_arriendo'].item(), parametros_iniciales['predial'].item(),
                                           valor_financiado,parametros_iniciales['seguro_vida'].item(),
                                           parametros_iniciales['seguro_it_amit'].item(),parametros_iniciales['prov_sostenimiento'].item(), valor_inmueble)

                if flujo_gasto is not None:
                    container_10 = st.container()
                    with container_10:
                        if (inversion_inicial != 0) and (tasa_credito != 0) and (plazo_credito_mes != 0):
                            st.markdown('Escenarios')
                            plan_pago = plan_pagos(valor_financiado,tasa_credito, plazo_credito_mes)
                            #st.write(plan_pago)
                            precalculotir = flujo_caja_tir(parametros_iniciales['comision_venta'].item(),parametros_iniciales['costo_not_venta'].item(),proyecto['Precio con descuento'].item(),
                                                           porcentaje_financiado,parametros_iniciales['retefuente_venta'].item(),plan_pago,
                                                           flujo_valorizacion,flujo_gasto,round(fecha_liq_inversion,0),valor_inicial_tir)


                            tir_MV = calcular_tir_MV(precalculotir.loc[0:fecha_liq_inversion * 12, 'flujo_caja_tir'])
                            tir_EA = calcular_tir_EA(tir_MV)
                            st.number_input('TIR Efectiva Anual', round(tir_EA * 100,3), format='%.2f', disabled=True)
                            st.number_input('TIR Mes Vencida', tir_MV * 100, disabled=True)
                            tir_7_ = tir_7()
                            if tir_7_ is not None:
                                tir_7_['Beneficio'] = inversion_inicial* tir_7_['TIR Efectiva Anual']/100
                                tir_7_['Beneficio acumulado'] = tir_7_['Beneficio'].cumsum()
                                tir_7_.drop([2022], axis=0, inplace=True)
                                st.dataframe(tir_7_.style.format({'TIR Efectiva Anual':'{:.2f}', 'TIR Mes Vencido':'{:.2f}',
                                                                  'Beneficio':'{:,.2f}', 'Beneficio acumulado':'{:,.2f}'},
                                                                 thousands='\''))
                                st.line_chart(tir_7_[['Beneficio', 'Beneficio acumulado']], height=200)
                                st.line_chart(tir_7_[['TIR Efectiva Anual', 'TIR Mes Vencido']], height=150)


                            col1, col2, col3, col4, col5 = st.columns(5)
                            with col1:
                                csv = convert_df(plan_pago)

                                st.download_button(
                                    "Descargar plan de pagos",
                                    csv,
                                    "file.csv",
                                    "text/csv",
                                    key='download-csv'
                                )
                            with col2:
                                csv = convert_df(flujo_valorizacion)

                                st.download_button(
                                    "Descargar flujo valorización",
                                    csv,
                                    "file.csv",
                                    "text/csv",
                                    key='download-csv')
                            with col3:
                                csv = convert_df(flujo_gasto)

                                st.download_button(
                                    "Descargar flujo Gastos",
                                    csv,
                                    "file.csv",
                                    "text/csv",
                                    key='download-csv')
                            with col4:
                                csv = convert_df(precalculotir)

                                st.download_button(
                                    "Descargar flujo TIR",
                                    csv,
                                    "file.csv",
                                    "text/csv",
                                    key='download-csv')












