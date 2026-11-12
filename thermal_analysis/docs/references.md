# References

To cite the tool, see `CITATION.cff` at the root of the KiCad/Icepak project.
Please also cite the method it implements: Székely 1997 and Székely and Van
Bien 1988 for the identification, Ben Hamed et al. 2024 for its use in the
automatic generation of thermal models.

The numbers [1] to [4] are those of `references.py`, used in the docstrings
of the code. A file name at the end of a reference is the copy of the
article in the `biblio/` folder of the stand-alone Zth_to_Foster tool.

Sorted by the name of the first author.

- Ben Hamed B., Ahmed A. S. E., Regnat G., Perrin R., Lefevre G., Buttay C.,
  Jay J., "Automatic Generation of Thermal Models for PCB-based Power
  Electronics", CIPS 2024, 13th International Conference on Integrated Power
  Electronics Systems, VDE Verlag, 2024. [2]
  <https://vde-verlag.de/proceedings-en/456288085.html>

- JEDEC JESD51-14, "Transient Dual Interface Test Method for the Measurement
  of the Thermal Resistance Junction-to-Case of Semiconductor Devices with
  Heat Flow Through a Single Path", 2010. [1] Measurement of $Z_{th}$ and use
  of structure functions.

- Lucy L. B., "An iterative technique for the rectification of observed
  distributions", Astronomical Journal, 79(6), 745-754, 1974.
  doi:10.1086/111605. One of the two original articles of the
  Richardson-Lucy deconvolution.

- Meshram M. S. S., "Iterative Richardson-Lucy Algorithm for the Modeling and
  Correction of Blurred Image with a Known Point Spread Function",
  International Journal of Engineering Research, 2(6), 2013. [3] Cited in
  `my_deconv`; an application to images, not a reference of the method.

- Poppe A., Parry J., "Thermal characterization of complex electronics: a
  basic primer on structure functions", 2016. [4] Reading of structure
  functions.

- Protonotarios E. N., Wing O., "Theory of nonuniform RC lines, Part I:
  Analytic properties and realizability conditions in the frequency domain",
  IEEE Transactions on Circuit Theory, 14(1), 2-12, 1967. Background of the
  time-constant representation of distributed RC lines.
  `biblio/Theory_of_Nonuniform_RC_Lines_Part_I_...pdf`

- Richardson W. H., "Bayesian-Based Iterative Method of Image Restoration",
  Journal of the Optical Society of America, 62(1), 55-59, 1972.
  doi:10.1364/JOSA.62.000055. The other original article of the
  Richardson-Lucy deconvolution.

- Savitzky A., Golay M. J. E., "Smoothing and Differentiation of Data by
  Simplified Least Squares Procedures", Analytical Chemistry, 36(8),
  1627-1639, 1964. Filter of `dZ_dln_t`.

- Székely V., "A new evaluation method of thermal transient measurement
  results", Microelectronics Journal, 28, 277-292, 1997. The
  time-constant spectrum, its computation by deconvolution, and the
  structure functions. `biblio/1-s2.0-S0026269296000316-main.pdf`

- Székely V., "Identification of RC networks by deconvolution: chances and
  limits", IEEE Transactions on Circuits and Systems I, 45(3), 244-258, 1998.
  doi:10.1109/81.662698. Limits of the method: resolution, noise.

- Székely V., Rencz M., "Thermal dynamics and the time constant domain",
  IEEE Transactions on Components and Packaging Technologies, 23(3),
  587-594, 2000. Time-constant spectrum and its uses.
  `biblio/Thermal_dynamics_and_the_time_constant_domain.pdf`

- Székely V., Van Bien T., "Fine structure of heat flow path in
  semiconductor devices: a measurement and identification method",
  Solid-State Electronics, 31(9), 1363-1368, 1988.
  doi:10.1016/0038-1101(88)90099-8. The network identification by
  deconvolution and the structure functions.
  `biblio/1-s2.0-0038110188900998-main.pdf`

- Ziegeler N. J., *PyRth*, Python package for thermal transient analysis.
  <https://github.com/nizie002/PyRth>, <https://pyrth.readthedocs.io>,
  doi:10.5281/zenodo.14965793. Structure functions of the window.

- Ziegeler N. J., Nolte P. W., Schweizer S., "Quantitative Performance
  Comparison of Thermal Structure Function Computations", Energies, 14(21),
  7068, 2021. doi:10.3390/en14217068. Compares deconvolution methods,
  including the Bayesian (Richardson-Lucy) one.

- Ziegeler N. J., Nolte P. W., Schweizer S., "Lanczos-based Foster-to-Cauer
  Transformation for Network Identification by Deconvolution", THERMINIC
  2024. doi:10.1109/THERMINIC62015.2024.10732055. Numerical conditioning of
  the Foster to Cauer conversion.
