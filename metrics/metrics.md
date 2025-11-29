# STEM and MTGS 

The script `metrics.py` contains code for both the STEM and MTGS metrics as reported in the paper. 

To run the `metrics.py` script please execute the following code:

```
import numpy as np
import argparse
from metrics import *

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='STEM and MTGS')
    parser.add_argument('--simth', type=float, default=0.5, help='Similarity Threshold Value')

    args = parser.parse_args()

    errors = evaluate_prediction(gt_steps, pred_steps, encode_texts, sim_threshold=args.simth)
```

The above `evaluate_prediction()` function expects two inputs `gt_steps` and `pred_steps` which should be a list of dictionary. The annotation in the dataset follows the same format. An example is shown below:

```
gt_steps = [
    {'text': 'Cook guanciale in a little oil until lightly browned but not crisp; remove from heat.', 'groundings': [(0, 428, 491), (2, 231, 297)]},
    {'text': 'Beat eggs with cheese to form a thick paste.', 'groundings': [(0, 428, 491)]},
    {'text': 'Cook pasta al dente, reserving starchy water.', 'groundings': [(0, 428, 491)]},
    {'text': 'Off heat, toss the pasta with guanciale and the egg-cheese mixture, adding a ladle of pasta water.', 'groundings': [(0, 428, 491)]},
    {'text': 'Stir confidently until creamy.', 'groundings': [(0, 428, 491)]}
]

pred_steps = [
    {'text': 'The chef is making a paste out of cheese and eggs.', 'groundings': [(0, 300, 305)]},
    {'text': 'He adds the egg and cheese mixture, pasta water, and tosses it.', 'groundings': [(0, 374, 380)]},
    {'text': 'Cook pasta al dente, reserving starchy water.', 'groundings': [(0, 431, 483)]},
    {'text': 'Stir confidently until creamy.', 'groundings': [(1, 123, 559)]}
]
```
