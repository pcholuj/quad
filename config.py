import logging

config = {
    'server' :{
        'host' : '',
        'port' : 3000
    },
    'logger' : {
        'name' : 'QuadLogger',
        'file' : 'qc.log',
        'levelConsole' : logging.INFO,
        'levelFile' : logging.WARNING,
        'formatterFile' : '[%(levelname)s] %(funcName)s: %(message)s',
        'formatterConsole' : '[%(levelname)s]:  %(message)s'
    },
    'motors': [{
            'pin' : 22,
            'name': 'Back Left',
            'rotation': 1,
            'dma' : 0 
        }, {
            'pin' : 17,
            'name': 'Front Left',
            'rotation': -1,
            'dma' : 1 
        }, {
            'pin' : 18,
            'name': 'Front Right',
            'rotation': 1,
            'dma' : 2 
        }, {
            'pin' : 23,
            'name': 'Back Right',
            'rotation': -1,
            'dma' : 3 
        }
    ],
}