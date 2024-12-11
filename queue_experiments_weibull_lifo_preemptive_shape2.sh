#/bin/sh

for LAMBD in 0.5 0.7 0.9 0.95 0.99; do
 for D in 1 2 5 10; do
    for shape in 0.5 1 2; do
        echo "lambda: " $LAMBD "d: " $D "shape: " $shape
        ./weibull_premptive_lifo2.py --shape $shape --lambd $LAMBD --d $D --n 10 --csv out_weibull_preemptive_lifo_shape2.csv --max-t 100_000
    done
 done
done
