"""W115.1 (B-094) evidence design: pooled, sequential evidence so leaves earn arms.

model.py      -- partial pooling of net-after-costs per arm over the leaf tree (exact Gaussian tree posterior).
sequential.py -- an always-valid e-process per tree node, so weekly looks do not inflate the error.
pipeline.py   -- rows -> looks -> posterior + e-process -> an arm per leaf (leaf map v2).
calendar.py   -- the date a leaf could first earn an arm at the current row rate.
Nothing here places, sizes or logs an order.
"""
