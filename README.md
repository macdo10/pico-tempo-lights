# pico-tempo-lights
Lights that light up according to EDF Tempo Tariff days - visualisation des jours Tempo d'EDF

To use this, you must get an API key. Create an account on French electricity transmission authority[RTE open data site](https://data.rte-france.com/), then create an app and subscribe it to the [Tempo Like Supply Contract API](https://data.rte-france.com/catalog/-/api/consumption/Tempo-Like-Supply-Contract/v1.1). Once you've done that, go to your application page (from My applications in the sidebar) and copy the base64 code which you'll need to authenticate your requests.

## Circuit

![Model](https://raw.githubusercontent.com/macdo10/pico-tempo-lights/main/tempo_circuit.png)

The Pi Pico needs a power input (not shown on circuit) - I use a 5v usb phone charger into the USB socket, but there are also battery possibilities.

See [my blog post](http://ifoundthisout.com/displaying-the-colours-of-edf-tarif-tempo-with-a-pico) for details about French electricity company EDF's Tempo contract. 
