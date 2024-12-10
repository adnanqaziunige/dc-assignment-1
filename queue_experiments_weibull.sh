#/bin/sh

for LAMBD in 0.5 0.7 0.9 0.95 0.99; do
 for D in 1 2 5 10; do
    for shape in 0.1 0.5 1 2 5; do
        echo $LAMBD $D $shape
        ./weibull.py --shape $shape --lambd $LAMBD --d $D --n 10 --csv out_weibull.csv --max-t 100_000
    done
 done
done
