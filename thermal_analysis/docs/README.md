# Thermal Impedance Analysis tool

The Thermal Impedance Analysis tool turns a thermal impedance curve
$Z_{th}(t)$ into compact thermal models: a Foster RC network, a Cauer RC
network and the structure functions. The whole tool, window and command
line, is the `thermal_analysis` package.

Fitting a Foster network by hand means guessing how many RC cells to use and
where their time constants lie, then adjusting them until the curve fits.
The tool finds both from the data, with the network identification by
deconvolution (NID) method of Székely, then refines the fit by least squares.

## Inputs and outputs

**Input.** A single thermal impedance curve $Z_{th}(t)$, with time in
seconds and impedance in K/W, supplied as an `.xlsx`, `.csv` or `.txt` file
or pasted from a spreadsheet.

**Outputs.**

- the Foster network: thermal resistance $R_k$ and time constant $\tau_k$ of
  each cell, with the reconstructed curve superimposed on the input data;
- the time-constant spectrum, which shows the distribution of the time
  constants;
- the equivalent Cauer network, with the cumulative and differential
  structure functions that describe the heat-flow path from the junction to
  the ambient;
- two LTspice models, one for the Foster network and one for the Cauer
  network, each with its symbol and its test bench;
- the results as tables, an Excel workbook, a CSV export and a PDF report.

Applied to the measured thermal impedance of an IGBT, the tool identifies a
seven-cell Foster network that reproduces the curve within 0.3 % of
$R_{th}$; the cumulative structure function ends at the measured thermal
resistance, 0.084 K/W.

## Where to start

- To install and start the tool, see [Installation](installation.md).
- To learn the tool, follow [Tutorial: first analysis of an IGBT measurement](tutorial.md).
- To do a specific task (prepare a file, edit the poles, export the
  results or the LTspice models, change a setting), see
  [How-to guides](howto.md).
- To understand what each step computes and its limits, read
  [How the identification works](method.md).
- If you used the stand-alone Zth_to_Foster tool, read
  [Differences with Zth_to_Foster](differences.md).
- When something fails, see [Troubleshooting](troubleshooting.md).

## All pages

Start here:

- [Installation](installation.md)
- [Tutorial: first analysis of an IGBT measurement](tutorial.md)
- [How-to guides](howto.md)

How it works:

- [How the identification works](method.md)
- [Validation](validation.md)

Reference:

- [Window, command line and files](reference.md)
- [Differences with Zth_to_Foster](differences.md)
- [Troubleshooting](troubleshooting.md)
- [Code reference](api.md)
- [References](references.md)
