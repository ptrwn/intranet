import click
from sqlalchemy.sql import exists
from main import Session, TrustedChats


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)


@cli.command()
@click.option('--only-chat-ids', is_flag=True, help='Show only chat ids')
def list(only_chat_ids):
    session = Session()
    q = session.query(TrustedChats).all()
    if only_chat_ids:
        res = []
        for id in q:
            res.append(id.chat_id)
        click.echo(res)
        return True
    for id in q:
        if id.name is None:
            click.echo("Chat ID: {}".format(id.chat_id))
        else:
            click.echo("Chat ID: {}, Name: {}".format(id.chat_id, id.name))
    session.close()


@cli.command()
@click.option('--id', help='Telegram chat id', type=int, required=True)
@click.option('--name', help='Telegram user name', type=str, default='')
def add(id, name):
    session = Session()
    q = session.query(TrustedChats).filter(TrustedChats.chat_id == str(id))
    if q.count():
        click.secho(click.style('ChatId must be unique.', fg='red',
                                blink=True), err=True)
        click.secho("Use \"list\" to see all trusted chat ids." )
    else:
        myobject = TrustedChats(chat_id=str(id), name=name)
        session.add(myobject)
        session.commit()
        click.echo('ChatId {} was added.'.format(id))
    session.close()

if __name__ == '__main__':
    cli(obj={})
