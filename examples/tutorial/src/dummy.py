from afml.context import run_ctx

import logging
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

logging.debug(f'Dataset: {run_ctx.dataset}')
logging.debug(f'Model: {run_ctx.model}')
if run_ctx.model is not None:
    print('> Building model with YAML params')
    model = run_ctx.model.build()
    model.summary()

    print('> Building model overriding params')
    model = run_ctx.model.build(input_size=42)
    model.summary()

    print('> Model method returned', run_ctx.model.module.model_method())
logging.debug(f'Params: {run_ctx.params}')
