import torch

# Define the settings for the sigmoid function scheduler
# Note: Do not include 'steps' in the settings as it gets added automatically.
# The settings dictionary should have the same names as the parameters in the get_sigmas function.
settings = {
    "name": "sigmoid",
    "settings": {
        # Format: "parameter_name": [type, default_value, min_value, max_value, step_value, round_flag]
        # Types supported: FLOAT, INT, STRING, BOOLEAN
        "sigma_max_sig": ["FLOAT", 16.0, 0.0, 5000.0, 0.01, False],
        "sigma_min_sig": ["FLOAT", 0.03, 0.0, 5000.0, 0.01, False],
        "steepness": ["FLOAT", 3.5, 0.0, 10.0, 0.01, False],
        "midpoint_ratio": ["FLOAT", 0.8, 0.0, 1.0, 0.01, False],
    }
}

# A scheduler must have a function called "get_sigmas" to work properly.
# The first input must be the steps for it to work properly as the steps setting is automatically added.
def get_sigmas(n, sigma_max_sig, sigma_min_sig, steepness=10, midpoint_ratio=0.5, device='cpu'):
    """
    Generates 'n' sigmas on an S-curve from sigma_max to sigma_min, with a controllable midpoint.
    
    Args:
    n (int): Number of sigmas to generate.
    sigma_min (float): Minimum value of sigma.
    sigma_max (float): Maximum value of sigma.
    steepness (float): Controls the steepness of the S-curve transition.
    midpoint_ratio (float): Determines where the midpoint of the S-curve is (0 to 1).
    device (str): Device to generate the sigmas on ('cpu' or 'cuda').

    Returns:
    torch.Tensor: A tensor of 'n' sigmas in descending order.
    """
    # Ensure midpoint_ratio is within bounds
    if not (0 <= midpoint_ratio <= 1):
        raise ValueError("midpoint_ratio must be between 0 and 1.")
    
    # Generate a range of values between -1 and 1
    x = torch.linspace(-1, 1, n, device=device)
    
    # Adjust the range of x to skew the sigmoid's midpoint
    x = steepness * (x + (2 * midpoint_ratio - 1))
    
    # Sigmoid function values
    sigmoids = 1 / (1 + torch.exp(-x))
    sigmoids = (sigmoids - sigmoids.min()) / (sigmoids.max() - sigmoids.min())
    
    # Scale the sigmoid output to the exact range [sigma_min_sig, sigma_max_sig]
    sigmas = sigma_max_sig - (sigma_max_sig - sigma_min_sig) * sigmoids
    
    return sigmas