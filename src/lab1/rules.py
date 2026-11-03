"""Hand-written rules. Both return a 0/1 numpy array."""
import numpy as np


def port_rule(df):
    """Alert on destination ports 21 (FTP) and 22 (SSH)."""
    return df["dport"].isin([21, 22]).values.astype(int)


def payload_rule(df, max_dur_us=1000):
    """Thursday rule: no payload in either direction and duration < 1,000 microseconds."""
    return ((df["TotLen Fwd Pkts"].values == 0) & (df["TotLen Bwd Pkts"].values == 0)
            & (df["Flow Duration"].values < max_dur_us)).astype(int)
