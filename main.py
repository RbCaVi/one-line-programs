import discord
import discord.ext.commands
import contextlib
import json
import os
import random
import string

import config

# https://stackoverflow.com/a/71169236

@contextlib.contextmanager
def command_group(bot, name, **kwargs):
  group = bot.create_group(name = name, **kwargs)
  yield CommandGroup(group)

def slash_command(bot, name, **kwargs):
  return bot.slash_command(name = name, guild_ids = config.guild_ids, **kwargs)

class CommandGroup:
  def __init__(self, group):
    self.group = group

  @contextlib.contextmanager
  def command_group(self, name, **kwargs):
    group = self.group.create_subgroup(name = name, **kwargs)
    yield CommandGroup(group)

  def slash_command(self, name, **kwargs):
    return self.group.command(name = name, guild_ids = config.guild_ids, **kwargs)

def json_load(file_name):
  with open(file_name) as f:
    return json.load(f)

def json_dump(data, file_name):
  with open(file_name, 'w') as f:
    json.dump(data, f, indent = 2)

class Projects:
  def __init__(self):
    self.projects = []
    for project_id in os.listdir(config.projects_data):
      try:
        self.projects.append(Project.load(project_id))
      except Exception as e:
        print(f'Could not load project at {project_id}.')
        print(f'Error: {repr(e)}')
    self.projects_by_channel_id = {p.channel_id: p for p in self.projects}
    self.projects_by_name = {p.name: p for p in self.projects}

  def __contains__(self, project):
    if isinstance(project, int):
      return project in self.projects_by_channel_id
    if isinstance(project, str):
      return project in self.projects_by_name
    return (
      project.channel_id in self.projects_by_channel_id or
      project.name in self.projects_by_name
    )

  def add(self, project):
    assert project not in self
    self.projects.append(project)
    self.projects_by_channel_id[project.channel_id] = project
    self.projects_by_name[project.name] = project

  def get(self, i):
    # get a project by either name or channel id
    if i in self.projects_by_channel_id:
      return self.projects_by_channel_id[i]
    elif i in self.projects_by_name:
      return self.projects_by_name[i]
    else:
      return None

  def __getitem__(self, i):
    # get a project by either name or channel id
    project = self.get(i)
    if project is None:
      raise ValueError(f'No project exists for key {repr(i)}')
    return project

class Project:
  def __init__(self, project_id, name, channel_id, focused_files):
    self.id = project_id
    self.name = name
    self.channel_id = channel_id
    self.files = []
    for file_id in os.listdir(os.path.join(config.projects_data, self.id, config.project_files)):
      try:
        self.files.append(File.load(self.id, file_id))
      except Exception as e:
        print(f'Could not load file at {project_name} :: {file_id}.')
        print(f'Error: {repr(e)}')
    self.files_by_name = {f.name: f for f in self.files}
    self.focused_files = {uid: self.files_by_name[name] for uid,name in focused_files}

  @staticmethod
  def load(project_id):
    project_data = json_load(os.path.join(config.projects_data, project_id, config.project_info))
    return Project(
      project_id = project_id,
      name = project_data['name'],
      channel_id = project_data['channel_id'],
      focused_files = project_data['focused_files'],
    )

  @staticmethod
  def new(name, channel):
    project_id = f'{name}_{channel.id}_{random_string()}'
    os.makedirs(os.path.join(config.projects_data, project_id, config.project_files))
    project = Project(
      project_id = project_id,
      name = name,
      channel_id = channel.id,
      focused_files = [],
    )
    project.files.append(File.new(project.id, 'main'))
    project.save()
    return project

  def save(self):
    json_dump({
      'name': self.name,
      'channel_id': self.channel_id,
      'focused_files': [[uid, f.name] for uid,f in self.focused_files.items()]
    }, os.path.join(config.projects_data, self.id, config.project_info))

  def add_file(self, name):
    self.files.append(File.new(self.id, name))

  def focus(self, user_id, name):
    self.focused_files[user_id] = self.files_by_name[name]

def random_string():
  return ''.join(random.choice(string.ascii_lowercase) for i in range(8))

def get_file_id(name):
  # how do i generate an id
  # idk just take name and put a "token" after it
  return name.replace('/', '_') + '_' + random_string()

def is_name_valid(name):
  return not any((
    name.startswith('/'),
    name.startswith('./'),
    name.startswith('../'),
    name.endswith('/'),
    name.endswith('/.'),
    name.endswith('/..'),
    '//' in name,
    '/./' in name,
    '/../' in name,
  ))

class File:
  def __init__(self, project_id, file_id, name, lines):
    self.project_id = project_id
    self.id = file_id
    self.name = name
    self.lines = [Line.load(l) for l in lines]

  @staticmethod
  def load(project_id, file_id):
    file_data = json_load(os.path.join(config.projects_data, project_id, config.project_files, file_id))
    return File(
      project_id = project_id,
      file_id = file_id,
      name = file_data['name'],
      lines = file_data['lines'],
    )

  @staticmethod
  def new(project_id, name):
    # create an empty file
    while os.path.exists(os.path.join(config.projects_data, project_id, config.project_files, file_id := get_file_id(name))): # this is the best way to write this
      pass
    file = File(
      project_id = project_id,
      file_id = file_id,
      name = name,
      lines = [],
    )
    file.save()
    return file

  def save(self):
    json_dump({
      'name': self.name,
      'lines': [l.dump() for l in self.lines],
    }, os.path.join(config.projects_data, self.project_id, config.project_files, self.id))

class Line:
  def __init__(self, content, contributors):
    self.content = content
    self.contributors = set(contributors)

  @staticmethod
  def load(line_data):
    return Line(
      content = line_data['content'],
      contributors = line_data['contributors'],
    )

  @staticmethod
  def new(content, author_id):
    return Line(
      content = content,
      contributors = [author_id],
    )

  def dump(self):
    return {
      'content': self.content,
      'contributors': list(self.contributors),
    }

bot = discord.ext.commands.Bot()

projects = Projects()

@slash_command(bot, 'first_slash')
async def first_slash(ctx):
  await ctx.respond('You executed the slash command first_slash!')

with command_group(bot, 'project') as projectgroup:
  @projectgroup.slash_command('new')
  async def project_new(ctx, name: str):
    if (existing_project := projects.get(ctx.channel.id)) is not None:
      await ctx.respond(f'A project has already been created in this channel: `{existing_project.name}`')
      return
    if (existing_project := projects.get(name)) is not None:
      await ctx.respond(f'A project has already been created with this name in <#{existing_project.channel_id}>')
      return
    new_project = Project.new(name, ctx.channel)
    projects.add(new_project)
    await ctx.respond(f'Project `{new_project.name}` created.')

  @projectgroup.slash_command('files')
  async def project_files(ctx):
    if (project := projects.get(ctx.channel.id)) is None:
      await ctx.respond('There is no project in this channel.')
      return
    files = '\n'.join('`' + file.name + '` (ID: `' + file.id + '`)' for file in project.files)
    await ctx.respond(f'Project `{project.name}` has {len(project.files)} files:\n{files}')

with command_group(bot, 'file') as filegroup:
  @filegroup.slash_command('new')
  async def file_new(ctx, name: str):
    if (project := projects.get(ctx.channel.id)) is None:
      await ctx.respond('There is no project in this channel.')
      return
    if not is_name_valid(name):
      await ctx.respond(f'`{name}` is not a valid filename.')
      return
    project.files.append(File.new(project.id, name))
    await ctx.respond(f'`{name}` has been created.')

  def autocomplete_file(ctx):
    if (project := projects.get(ctx.interaction.channel.id)) is None:
      return []
    return [name for name in project.files_by_name if name.lower().startswith(ctx.value.lower())]

  def file_option(name):
    return discord.Option(name = name, autocomplete = autocomplete_file)

  @filegroup.slash_command('focus', options = [file_option('name')])
  async def file_focus(ctx, name: str):
    if (project := projects.get(ctx.channel.id)) is None:
      await ctx.respond('There is no project in this channel.')
      return
    if name not in project.files_by_name:
      await ctx.respond(f'`{name}` does not exist in this project.')
      return
    project.focus(ctx.author.id, name)
    project.save()
    await ctx.respond(f'File `{name}` focused.')

  @filegroup.slash_command('view', options = [file_option('name')])
  async def file_view(ctx, name: str):
    if (project := projects.get(ctx.channel.id)) is None:
      await ctx.respond('There is no project in this channel.')
      return
    if name not in project.files_by_name:
      await ctx.respond(f'`{name}` does not exist in this project.')
      return
    await ctx.respond('You executed the slash command view_file!')

  @filegroup.slash_command('delete')
  async def file_delete(ctx):
    if (project := projects.get(ctx.channel.id)) is None:
      await ctx.respond('There is no project in this channel.')
      return
    await ctx.respond('You executed the slash command delete_file!')

with command_group(bot, 'statement') as statementgroup:
  @statementgroup.slash_command('add')
  async def statement_add(ctx, line_num: int, content: str):
    if (project := projects.get(ctx.channel.id)) is None:
      await ctx.respond('There is no project in this channel.')
      return
    if (file := project.focused_files.get(ctx.author.id)) is None:
      await ctx.respond('You are not focused on a file.')
      return
    if line_num < 0:
      line_num = 0
    if line_num > len(file.lines):
      line_num = len(file.lines)
    file.lines.insert(line_num, Line.new(content, ctx.author.id))
    file.save()
    await ctx.respond('Statement added.')

  @statementgroup.slash_command('edit')
  async def statement_edit(ctx, line_num: int, new_content: str):
    if (project := projects.get(ctx.channel.id)) is None:
      await ctx.respond('There is no project in this channel.')
      return
    if (file := project.focused_files.get(ctx.author.id)) is None:
      await ctx.respond('You are not focused on a file.')
      return
    if line_num < 1 or line_num > len(file.lines):
      await ctx.respond('Invalid line number.')
      return
    line = file.lines[line_num]
    poll = discord.Poll(
      question = discord.PollMedia(f'Edit line `{line_num}` of `{file.name}` (currently `{line.content}`) to `{new_content}`?'),
      answers = [
        discord.PollAnswer("Yes", "❤️"),
        discord.PollAnswer("No", "💔"),
      ],
      duration = 1,
      allow_multiselect = False,
    )
    message = await ctx.respond('You executed the slash command edit_statement!', poll = poll)
    line.add_edit_poll(message, ctx.author.id, new_content)

  @statementgroup.slash_command('delete')
  async def statement_delete(ctx, line_num: int):
    if (project := projects.get(ctx.channel.id)) is None:
      await ctx.respond('There is no project in this channel.')
      return
    if (file := project.focused_files.get(ctx.author.id)) is None:
      await ctx.respond('You are not focused on a file.')
      return
    if line_num < 1 or line_num > len(file.lines):
      await ctx.respond('Invalid line number.')
    line = file.lines[line_num]
    poll = discord.Poll(
      question = discord.PollMedia(f'Delete line `{line_num}` of `{file.name}` (`{line.content}`)?'),
      answers = [
        discord.PollAnswer("Yes", "💔"),
        discord.PollAnswer("No", "❤️"),
      ],
      duration = 1,
      allow_multiselect = False,
    )
    message = await ctx.respond('You executed the slash command delete_statement!', poll = poll)
    line.add_delete_poll(message, ctx.author.id)

@bot.event
async def on_ready() -> None:
  print(f"I am {bot.user}.")
  assert bot.user is not None
  print(f"Others may know me as {bot.user.display_name}.")
  print(f"ID: {bot.user.id}")

@bot.event
async def on_raw_poll_vote_add(payload) -> None:
  print(payload)
  poll = (await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)).poll
  print(poll.total_votes())
  for answer in poll.answers:
    print(answer, await [x async for x in answer.voters()])

with open('token') as f:
  token = f.read()

bot.run(token)
