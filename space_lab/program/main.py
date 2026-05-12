import time
start_time = time.perf_counter()

import numpy as np
import math
from picamzero import Camera
from astro_pi_orbit import ISS

import camera_distortion
from writeResult import write_result
import calculateSpeed

TIME_INTERVAL = 13
IMAGE_COUNT = 42
MAX_TIME_ELAPSED = 570  # 9.5 minutes

def capture_images():
    """
    Captures half the total images before calculating anything to calculate the stability mask.
    Then in the second half calculates the speeds from all images
    """
    cam = Camera()
    results = []
    images = []
    timestamps = []
    altitudes = []
    latitudes = []

    def process_image_pair(img1, img2, i):
        time_diff = timestamps[i] - timestamps[i - 1]
        try:
            # Uses altitude and latitude of img1 by convention
            iss_altitude = altitudes[i - 1]
            iss_latitude = latitudes[i - 1]
            speed, inliers = calculateSpeed.calculate(img1, img2, time_diff, iss_altitude, math.radians(iss_latitude))

            results.append({
                "speed": speed,
                "confidence": inliers
            })
        except Exception as e:
            print(f"Calculation error at index {i}: {e}")

    half_of_image_count = IMAGE_COUNT // 2
    shape = camera_distortion.get_dimensions()
    calculateSpeed.initiate_stability_mask(half_of_image_count, shape[1], shape[0])

    # Capture images, but does not calculate anything
    for i in range(half_of_image_count):
        if time.perf_counter() - start_time > MAX_TIME_ELAPSED:
            print("Time limit reached. Breaking loop.")
            break
        cycle_start = time.perf_counter()

        image_path = f"image{i}.jpg"
        capture_start = time.perf_counter()
        cam.take_photo(image_path)

        images.append(camera_distortion.undistort_image(image_path))
        timestamps.append(capture_start)
        altitudes.append(ISS().coordinates().elevation.m)
        latitudes.append(ISS().coordinates().latitude.degrees)

        calculateSpeed.add_to_mask(images[i], True)

        elapsed_in_cycle = time.perf_counter() - cycle_start
        sleep_time = max(0.0, TIME_INTERVAL - elapsed_in_cycle)

        if elapsed_in_cycle > TIME_INTERVAL:
            print(f"WARNING: Cycle {i} exceeded TIME_INTERVAL! Timing may be drifting.")

        np.savetxt("timestamps.csv", timestamps, delimiter=",", header="timestamps", comments='')
        time.sleep(sleep_time)

    # Captures images and calculates previously taken images
    for i in range(half_of_image_count, IMAGE_COUNT, 1):
        if time.perf_counter() - start_time > MAX_TIME_ELAPSED:
            print("Time limit reached. Breaking loop.")
            break

        cycle_start = time.perf_counter()

        if i - half_of_image_count < half_of_image_count:
            img1 = images[i - half_of_image_count]
            img2 = images[i - half_of_image_count + 1]
            process_image_pair(img1, img2, i - half_of_image_count + 1)

        image_path = f"image{i}.jpg"
        capture_start = time.perf_counter()
        cam.take_photo(image_path)

        images.append(camera_distortion.undistort_image(image_path))
        timestamps.append(capture_start)
        altitudes.append(ISS().coordinates().elevation.m)
        latitudes.append(ISS().coordinates().latitude.degrees)

        if time.perf_counter() - start_time > MAX_TIME_ELAPSED:
            print("Time limit reached. Breaking loop.")
            break

        img1 = images[i - 1]
        img2 = images[i]
        process_image_pair(img1, img2, i)

        elapsed_in_cycle = time.perf_counter() - cycle_start
        sleep_time = max(0.0, TIME_INTERVAL - elapsed_in_cycle)

        if elapsed_in_cycle > TIME_INTERVAL:
            print(f"WARNING: Cycle {i} exceeded TIME_INTERVAL! Timing may be drifting.")

        np.savetxt("timestamps.csv", timestamps, delimiter=",", header="timestamps", comments='')
        time.sleep(sleep_time)

    if not results:
        print("No results collected.")
        return 0

    results.sort(key=lambda x: x["confidence"], reverse=True)
    # Takes the median of 25 % of images with the most inliers according to RANSAC
    top_n = max(1, len(results) // 4)
    best_results = results[:top_n]

    final_speeds = [res["speed"] for res in best_results]
    avg_speed = np.median(final_speeds)

    print(f"Final Average Speed: {avg_speed:.4f}")

    del cam
    return avg_speed

def main():
    try:
        speed = capture_images()
        write_result(speed)
    except Exception as e:
        print(f"Fatal error: {e}")
        write_result(0)

if __name__ == "__main__":
    main()