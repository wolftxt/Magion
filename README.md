# Magion — ISS Motion Measurement

**Magion** was developed in partial fulfilment of the requirements for my high school graduation.

The program processes image pairs using OpenCV camera calibration, static masking, and ORB keypoint tracking, applying WGS 84 spherical geometry and correcting for Earth's rotation to convert pixel displacements into real world speed.

## Results
On the ISS the program calculated its speed as 7.5434 km/s, which is within 1.5% of the actual average ISS orbital speed (~7.66 km/s).

## Documentation
Documentation is found in the [full project paper](documentation.pdf).
